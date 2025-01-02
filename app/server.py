from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage, NEXT_AVAILABLE_SESSION
import asyncio
import json
import random
import os
import dotenv
dotenv.load_dotenv()

CONNECTION_STR = os.getenv("SERVICEBUS_CONNECTION_STRING")
REQUEST_QUEUE_NAME = os.getenv("SERVICEBUS_REQUEST_QUEUE_NAME")
RESPONSE_QUEUE_NAME = os.getenv("SERVICEBUS_RESPONSE_QUEUE_NAME")

async def process_batch_job(message_content):
    try:
        data = json.loads(message_content)
    except:
        data = {"message": message_content}
    
    await asyncio.sleep(random.randint(1, 5))
    
    result = {
        "status": "completed",
        "input": data,
        "result": f"작업 처리 완료: {data}"
    }
    
    return json.dumps(result)

async def handle_message(servicebus_client, sender, queue_name):
    try:
        async with servicebus_client.get_queue_receiver(
            queue_name=queue_name,
            session_id=NEXT_AVAILABLE_SESSION,
            max_wait_time=50
        ) as receiver:
            print(f"세션 연결됨: {receiver.session.session_id}")
            await receiver.session.set_state("OPEN")
            async for message in receiver:
                try:
                    print(f"\n새 메시지 수신: {message.session_id} - {str(message)}")
                    
                    result = await process_batch_job(str(message))
                    response = ServiceBusMessage(result, session_id=message.session_id)
                    await sender.send_messages(response)
                    
                    await receiver.complete_message(message)
                    print(f"응답 전송 완료: {result}")
                    await receiver.session.set_state("CLOSED")
                    return
                    
                except Exception as msg_error:
                    print(f"메시지 처리 중 에러: {str(msg_error)}")
                    await receiver.session.set_state("ERROR")
                    await receiver.abandon_message(message)
                    return
            print(f"세션 닫힘: {receiver.session.session_id}")
    except Exception as session_error:
        print(f"세션 처리 중 에러: {str(session_error)}")
        return


async def server_main():
    print(f"서비스 버스 연결 시작...")
    print(f"연결 문자열: {CONNECTION_STR[:50]}...")
    
    # 활성 작업 추적을 위한 세트
    active_tasks = set()
    MAX_WORKERS = 5  # 최대 동시 처리 작업 수
    
    async with ServiceBusClient.from_connection_string(CONNECTION_STR) as servicebus_client:
        async with servicebus_client.get_queue_sender(queue_name=RESPONSE_QUEUE_NAME) as sender:
            while True:
                try:
                    # 완료된 작업 제거
                    done_tasks = {task for task in active_tasks if task.done()}
                    active_tasks.difference_update(done_tasks)
                    
                    # 새로운 작업 추가
                    while len(active_tasks) < MAX_WORKERS:
                        print(f"새 작업 생성: {len(active_tasks) + 1} / {MAX_WORKERS}")
                        task = asyncio.create_task(
                            handle_message(servicebus_client, sender, REQUEST_QUEUE_NAME)
                        )
                        active_tasks.add(task)
                    
                    # 잠시 대기 후 다음 체크
                    await asyncio.sleep(1)
                    
                    # 에러 체크 (선택적)
                    for task in active_tasks:
                        if task.done() and task.exception():
                            print(f"작업 에러 발생: {task.exception()}")
                    
                except Exception as e:
                    print(f"메인 루프 에러 발생: {str(e)}")
                    await asyncio.sleep(1)

def main():
    try:
        print("서버 시작...")
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\n서버 종료...")
    except Exception as e:
        print(f"예상치 못한 에러 발생: {str(e)}")

if __name__ == "__main__":
    main()
