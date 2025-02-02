import asyncio
import json
import os
from datetime import datetime
import logging

import dotenv
from azure.servicebus.aio import ServiceBusClient, ServiceBusSender
from azure.servicebus import ServiceBusMessage, NEXT_AVAILABLE_SESSION
from asyncio.tasks import Task

from service.batch_service import BatchClient
from repository.task_repository import RedisConnector
from dto import BatchRequest, BatchResponse
from utils.teams_alert import send_alert
from config.servicebus_config import ServiceBusConfig

dotenv.load_dotenv()


class ServiceBusServer:
    def __init__(self):
        self.max_workers: int = 2
        self.active_tasks: set[Task] = set()
        self.batch_client: BatchClient = BatchClient()
        self.redis: RedisConnector = RedisConnector()
        self.servicebus_config: ServiceBusConfig = ServiceBusConfig()

    async def start(self) -> None:
        """서버 시작 시 초기화 및 작업 복구"""
        logging.info("Initialize server...")
        await self.recover_active_tasks()
        await self.run()

    async def stop(self) -> None:
        """서버 종료"""
        logging.info("Terminate server...")
        await self.redis.close()

    async def save_task_state(self, task_id: str, state: dict) -> None:
        """작업 상태를 Redis에 저장"""
        logging.info(f"Save request state at Redis: {task_id}")
        await self.redis.save_task_state(task_id, state)


    async def remove_task_state(self, task_id: str) -> None:
        """완료된 작업 상태를 Redis에서 제거"""
        logging.info(f"Remove request from Redis: {task_id}")
        await self.redis.remove_task_state(task_id)


    async def recover_active_tasks(self) -> None:
        """Redis에서 이전 작업 상태 복구"""
        stored_tasks = await self.redis.get_all_tasks()

        async with ServiceBusClient.from_connection_string(self.servicebus_config.connection_str) as servicebus_client:
            async with servicebus_client.get_queue_sender(queue_name=self.servicebus_config.response_queue) as sender:
                for task_id, state in stored_tasks.items():
                    try:
                        logging.info(f"Restore saved requests from Redis: {task_id}")
                        task = asyncio.create_task(
                            self.handle_message(
                                servicebus_client=servicebus_client,
                                sender=sender,
                                queue_name=self.servicebus_config.request_queue,
                                recovery_state=state,
                            )
                        )
                        self.active_tasks.add(task)
                        await task
                        await send_alert(f"Restored request from Redis success: {task_id}")
                        logging.info(f"Restored request from Redis success: {task_id}")
                    except Exception as e:
                        await send_alert(f"Restored request from Redis failed: {task_id}")
                        logging.error(f"Resotring request from Redis failed {task_id}: {str(e)}")

    async def handle_message(
        self,
        servicebus_client: ServiceBusClient,
        sender: ServiceBusSender,
        queue_name: str,
        recovery_state: str | None = None,
    ) -> None:
        """메시지 처리 (복구 상태 포함)"""
        try:
            if recovery_state:
                # 복구된 상태에서 BatchRequest 생성
                request = BatchRequest.from_dict(recovery_state)
                result_paths = await self.batch_client.run(
                    request.session_id,
                    request.timestamp,
                    request.command,
                )

                response = BatchResponse(session_id=request.session_id, result_paths=result_paths, status="completed")

                # Service Bus 메시지로 변환하여 전송
                message = ServiceBusMessage(json.dumps(response.to_dict()), session_id=response.session_id)
                await sender.send_messages(message)
                await self.remove_task_state(request.session_id)

                logging.info(f"Session closed: {request.session_id}")

            else:
                async with servicebus_client.get_queue_receiver(
                    queue_name=queue_name, session_id=NEXT_AVAILABLE_SESSION, max_wait_time=100
                ) as receiver:
                    await receiver.session.set_state("OPEN")
                    status = await receiver.session.get_state()
                    logging.info(f"Session connected: {receiver.session.session_id}: {status}")

                    async for message in receiver:
                        try:
                            # 수신된 메시지를 BatchRequest로 변환
                            request = BatchRequest.from_dict(json.loads(str(message)))
                            logging.info(f"Run Batch with new request: {request}")

                            # 메시지 완료 처리
                            await receiver.complete_message(message)
                            logging.info(f"\nNew message received: {request}")

                            # Redis에 작업 상태 저장
                            await self.save_task_state(request.session_id, request.to_dict())

                            result_paths = await self.batch_client.run(
                                request.session_id,
                                request.timestamp,
                                request.command,
                            )

                            response = BatchResponse(
                                session_id=request.session_id, result_paths=result_paths, status="completed"
                            )

                            # response를 직렬화
                            message = ServiceBusMessage(json.dumps(response.to_dict()), session_id=response.session_id)
                            await sender.send_messages(message)

                            logging.info(f"Message sent successfully: {response}")

                            # Redis에서 작업 상태 제거
                            await self.remove_task_state(receiver.session.session_id)

                            # 세션 종료
                            await receiver.session.set_state("CLOSED")
                            status = await receiver.session.get_state()
                            logging.info(f"Session closed: {receiver.session.session_id}: {status}")
                            await self.send_alert(f"Batch request success: {response}")
                            return

                        except Exception as msg_error:
                            error_response = BatchResponse(
                                session_id=request.session_id,
                                result_paths="",
                                status="error",
                                error_message=str(msg_error),
                            )
                            logging.error(msg_error)
                            # 에러 응답도 JSON 직렬화
                            error_message = ServiceBusMessage(
                                json.dumps(error_response.to_dict()), session_id=request.session_id
                            )
                            await sender.send_messages(error_message)
                            await self.send_alert(f"Batch request failed: {error_response}")
                            return

        except Exception as e:
            logging.error(f"Error while handling the message: {str(e)}")
            if recovery_state:
                error_state = {
                    **recovery_state,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                await self.save_task_state(recovery_state["session_id"], error_state)

            raise

    async def run(self) -> None:
        logging.info(f"Connect to ServiceBus...")

        async with ServiceBusClient.from_connection_string(self.servicebus_config.connection_str) as servicebus_client:
            async with servicebus_client.get_queue_sender(queue_name=self.servicebus_config.response_queue) as sender:
                while True:
                    try:
                        # 완료된 작업 제거
                        done_tasks = {task for task in self.active_tasks if task.done()}
                        self.active_tasks.difference_update(done_tasks)

                        # 새로운 작업 추가 (여기서는 recovery_state=None)
                        while len(self.active_tasks) < self.max_workers:
                            task = asyncio.create_task(
                                self.handle_message(
                                    servicebus_client=servicebus_client,
                                    sender=sender,
                                    queue_name=self.servicebus_config.request_queue,
                                )
                            )
                            self.active_tasks.add(task)

                        await asyncio.sleep(1)

                    except Exception as e:
                        logging.error(f"An error occurred in the main loop: {str(e)}")
                        await asyncio.sleep(1)


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(funcName)s %(levelname)s:%(message)s", level=logging.INFO)
    server = ServiceBusServer()
    try:
        logging.info("Server starts...")
        asyncio.run(server.start())

    except KeyboardInterrupt:
        logging.info("Server shutting down...")
        asyncio.run(server.stop())

    except Exception as e:
        logging.error(f"An unexpected error has occurred: {str(e)}")


if __name__ == "__main__":
    main()
