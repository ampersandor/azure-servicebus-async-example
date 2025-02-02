import asyncio
import os
import logging
import hashlib

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
)
from azure.batch import BatchServiceClient
from azure.batch.batch_auth import SharedKeyCredentials

from src.repository.session_repository import SessionRepository
from src.repository.result_repository import ResultRepository

from src.config.batch_config import BatchConfig

class BatchClient:
    def __init__(self):
        self.session_repo = SessionRepository()
        self.result_repo = ResultRepository()

        self.batch_client = BatchServiceClient(
            credentials=SharedKeyCredentials(BatchConfig.account_name, BatchConfig.account_key),
            batch_url=BatchConfig.account_url,
        )
        self.batch_mount_path = os.getenv("BATCH_MOUNT_PATH")
        self.batch_output_path = "output"
        self.server_mount_path = os.getenv("SERVER_MOUNT_PATH")
        self.pool_id = BatchConfig.pool_id

    async def run(
        self,
        session_id: str,
        command: str,
    ) -> list[str]:
        try:
            job_id = self._create_job_hash(command)
            # job_id session id 별로 저장
            await self._save_session_id(session_id, job_id)

            # Check DB for existing results
            existing_result = await self._check_existing_result(job_id)
            if existing_result:
                return existing_result

            # Create and submit batch job
            output_dir = os.path.join(self.batch_output_path, job_id)
            job_result = await self._process_batch_job(
                os.path.join(self.batch_mount_path, output_dir),
                job_id,
                command,
            )

            await self._save_results(job_id, job_result)

            return job_result

        except Exception as e:
            logging.error(str(e))
            raise BatchProcessingError(f"Batch processing failed: {str(e)}")

    def _create_job_hash(
        self,
        command: str,
    ) -> str:
        """Create unique hash for job based on command"""
        return hashlib.md5(command.encode("utf-8")).hexdigest()

    async def _check_existing_result(self, job_id: str) -> str:
        """Check database for existing results"""
        return await self.result_repo.get_result(job_id)

    async def _save_session_id(self, session_id: str, job_id: str) -> str:
        """save session_id and job_id to database"""
        return await self.session_repo.save_session_id({"session_id": session_id, "job_id": job_id})

    async def _process_batch_job(
        self,
        output_dir: str,
        job_id: str,
        command: str,
    ) -> list[str]:
        """Create and manage batch job with multiple tasks"""
        job_name = None

        try:
            # Create Azure Batch Job
            self._create_batch_job(job_id)

            # Create Azure Batch Tasks
            tasks = []
            tasks.append(
                self._create_batch_task(output_dir, job_id, command)
            )

            results = await asyncio.gather(*tasks)

            return results

        except Exception as e:
            raise e

        finally:
            if job_name:
                self._terminate_batch_job(job_name)

    def _create_batch_job(self, job_id: str) -> None:
        """Create Azure Batch Job with job_id as job ID"""

        try:
            self.batch_client.job.get(job_id=job_id)
            logging.info(f"Job already exists in Batch pool: {job_id}")

        except BatchErrorException:
            job = JobAddParameter(id=job_id, pool_info=PoolInformation(pool_id=self.pool_id))
            self.batch_client.job.add(job)
            logging.info(f"Job creation success {job_id}")

        except Exception as e:
            raise (e)

        return

    def _terminate_batch_job(self, job_id: str) -> None:
        """Remove completed Batch BATCH Job"""
        try:
            self.batch_client.job.terminate(job_id=job_id)

        except BatchErrorException as e:
            raise e

        except Exception as e:
            raise e

    async def _create_batch_task(
        self,
        output_dir: str,
        job_id: str,
        command: str,
    ) -> str:
        task_id = f"Task_{job_id}"

        try:
            self.batch_client.task.get(job_id, task_id)
            logging.info(f"Batch Task already exists: {job_id} | {task_id}")
        except BatchErrorException:
            batch_task = TaskAddParameter(
                id=task_id,
                command_line=command,
                user_identity=UserIdentity(
                    auto_user=AutoUserSpecification(scope=AutoUserScope.pool, elevation_level=ElevationLevel.admin)
                ),
            )

            self.batch_client.task.add(job_id, batch_task)

        except Exception as e:
            raise (e)

        while True:
            batch_task = self.batch_client.task.get(job_id, task_id)
            task_state = batch_task.state

            if task_state == TaskState.completed:
                execution_info = batch_task.execution_info

                if execution_info.result == "success":
                    break

                else:
                    failure_info = execution_info.failure_info
                    raise BatchProcessingError(f"Task {task_id} failed. Error: {failure_info.message}")

            await asyncio.sleep(1)

        return 0


    async def _save_results(self, job_id: str, result_path: str) -> None:
        """Save results to database"""
        await self.sql_connector.save_job_result({"job_id": job_id, "result_path": result_path})


class BatchProcessingError(Exception):
    pass
