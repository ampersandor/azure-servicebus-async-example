import asyncio
import os
import logging
import traceback
import hashlib
from src.models.request import Request
from azure.batch.models import (
    TaskAddParameter,
    UserIdentity,
    AutoUserSpecification,
    AutoUserScope,
    ElevationLevel,
    TaskState,
    JobAddParameter,
    PoolInformation,
    BatchErrorException,
    TaskConstraints,
    OutputFileDestination,
    OutputFileBlobContainerDestination,
    OutputFileUploadOptions,
    OutputFile
)
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials

from src.repository.result_repository import ResultRepository
from src.models.result import ResultStatus
from src.config.batch_config import BatchConfig
from src.config.blob_config import BlobConfig
from src.exceptions import *
from src.repository.request_result_repository import RequestResultRepository


class BatchService:
    def __init__(self):
        self.result_repo = ResultRepository()
        self.request_result_repo = RequestResultRepository()
        self.batch_client = BatchServiceClient(
            credentials=SharedKeyCredentials(BatchConfig.account_name, BatchConfig.account_key),
            batch_url=BatchConfig.account_url,
        )
        self.batch_output_path = os.getenv("BATCH_MOUNT_PATH")
        self.server_mount_path = os.getenv("SERVER_MOUNT_PATH")
        self.blob_url = BlobConfig.BLOB_URL
        self.blob_dir = "output"
        self.pool_id = BatchConfig.pool_id

    async def run(self, request: Request) -> str:
        """Execute batch job and return result path"""
        result_id = hashlib.md5(request.command.encode()).hexdigest()
        
        try:
            # Check existing result
            existing_result = await self.result_repo.get_result(result_id)
            if existing_result and existing_result.status == ResultStatus.COMPLETED:
                await self.request_result_repo.create_relation(
                    request_id=request.request_id,
                    result_id=result_id
                )
                return existing_result.result_path

            # Create initial result
            await self.result_repo.create_result(result_id)
            
            # Create relation
            await self.request_result_repo.create_relation(
                request_id=request.request_id,
                result_id=result_id
            )
            
            # Process batch job
            result_path = await self._process_batch_job(result_id, request.command)
            return result_path

        except BatchServiceError as e:
            # Known errors are logged and re-raised
            logging.error(f"Batch service error: {str(e)}")
            raise
        except Exception as e:
            # Unexpected errors are wrapped
            logging.error(f"Unexpected error: {str(e)}")
            raise BatchServiceError(f"Unexpected error during batch execution: {str(e)}")

    async def _process_batch_job(self, result_id: str, command: str) -> str:
        """Process batch job and return result path"""
        try:
            # Create job
            await self._create_batch_job(result_id)

            # Create and execute task
            task_id = await self._create_batch_task(result_id, command)
            await self.result_repo.update_status(result_id, ResultStatus.RUNNING)

            # Get result
            result_path = await self._get_task_result(result_id, task_id)
            await self.result_repo.update_result_path(result_id, result_path)
            
            return result_path

        except Exception as e:
            await self.result_repo.update_status(result_id, ResultStatus.FAILED)
            raise BatchJobError(f"Failed to process batch job: {str(e)}")

        finally:
            try:
                self._terminate_batch_job(result_id)
                await self.result_repo.update_status(result_id, ResultStatus.COMPLETED)
            except Exception as e:
                logging.error(f"Error during job cleanup: {str(e)}")

    async def _create_batch_job(self, result_id: str) -> None:
        try:
            job = JobAddParameter(
                id=result_id, 
                pool_info=PoolInformation(pool_id=self.pool_id)
            )
            self.batch_client.job.add(job)
            
        except BatchErrorException as e:
            raise BatchJobError(f"Failed to create batch job: {str(e)}")

    # does not support async in azure sdk
    def _terminate_batch_job(self, result_id: str) -> None:
        """Remove completed Batch Job"""
        try:
            self.batch_client.job.terminate(job_id=result_id)

        except BatchErrorException as e:
            raise BatchJobError(f"Failed to terminate batch job: {str(e)}")

    async def _create_batch_task(self, job_id: str, command: str) -> str:
        task_id = "task"

        try:
            # stdout 파일 설정
            output_file = OutputFile(
                file_pattern="*.txt",  # 모든 txt 파일 매칭
                destination=OutputFileDestination(
                    container=OutputFileBlobContainerDestination(
                        container_url=self.blob_url,
                        path=f"{job_id}"
                    )
                ),
                upload_options=OutputFileUploadOptions(
                    upload_condition="taskCompletion"
                )
            )

            # 작업 디렉토리에서 명령어 실행하고 출력을 파일로 저장
            modified_command = (
                'bash -c \''
                'cd $AZ_BATCH_TASK_WORKING_DIR && '  # 작업 디렉토리로 이동
                f'{command} > output.txt 2>&1 && '   # 표준 출력과 에러를 같은 파일로
                'cat output.txt\''                   # 출력 확인용
            )

            batch_task = TaskAddParameter(
                id=task_id,
                command_line=modified_command,
                user_identity=UserIdentity(
                    auto_user=AutoUserSpecification(
                        scope=AutoUserScope.pool,
                        elevation_level=ElevationLevel.admin
                    )
                ),
                output_files=[output_file],
                constraints=TaskConstraints(
                    max_wall_clock_time="PT1H",
                    retention_time="PT1H",
                    max_task_retry_count=1
                )
            )

            self.batch_client.task.add(job_id, batch_task)
            logging.info(f"Batch task creation success: {task_id}")
            return task_id

        except BatchErrorException as e:
            logging.error(f"Batch task creation failed: {str(e)}")
            raise BatchTaskError(f"Failed to create batch task: {str(e)}")

    async def _get_task_result(self, job_id: str, task_id: str) -> str:
        try:
            while True:
                task = self.batch_client.task.get(job_id, task_id)
                if task.state == TaskState.completed:
                    if task.execution_info.result == "success":
                        return os.path.join(self.blob_url, f"{job_id}/output.txt")
                    else:
                        raise TaskExecutionError(
                            f"Task failed: {task.execution_info.failure_info.message}"
                        )
                await asyncio.sleep(1)
                
        except BatchErrorException as e:
            raise BatchTaskError(f"Failed to get task result: {str(e)}")
