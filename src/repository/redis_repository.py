from redis import asyncio as aioredis
import json
from typing import Dict, Optional
import logging

from src.config.redis_config import RedisConfig


class RedisConnector:
    def __init__(self):
        self.redis = aioredis.Redis(
            host=RedisConfig.host, 
            port=RedisConfig.port,
            password=RedisConfig.password,
            decode_responses=True,
            ssl=False
        )
    async def save_task_state(self, task_id: str, state: dict):
        """작업 상태를 Redis에 저장"""
        try:
            await self.redis.hset(
                "active_tasks",
                task_id,
                json.dumps(state)
            )
        except Exception as e:
            logging.error(f"Redis save error: {e}")
            raise

    async def remove_task_state(self, task_id: str):
        """완료된 작업 상태를 Redis에서 제거"""
        await self.redis.hdel("active_tasks", task_id)

    async def get_all_tasks(self) -> Dict:
        """모든 활성 작업 상태 조회"""
        try:
            tasks = await self.redis.hgetall("active_tasks")
            return {
                task_id: json.loads(state)
                for task_id, state in tasks.items()
            }
        except Exception as e:
            logging.error(f"Redis get error: {e}")
            raise

    async def get_task_state(self, task_id: str) -> Optional[Dict]:
        """특정 작업의 상태 조회"""
        state = await self.redis.hget("active_tasks", task_id)
        return json.loads(state) if state else None

    async def flush_all(self):
        """모든 데이터 삭제 (테스트용)"""
        await self.redis.flushall()

    async def close(self):
        """Redis 연결 종료"""
        await self.redis.close() 