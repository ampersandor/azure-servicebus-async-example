from redis import asyncio as aioredis
import json
from typing import Dict, Optional
import os

class RedisConnector:
    def __init__(self, config: Optional[Dict] = None):
        if config is None:
            config = {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": os.getenv("REDIS_PORT", 6379),
                "password": os.getenv("REDIS_PASSWORD", "pw"),
                "encoding": "utf-8",
                "decode_responses": True
            }
        
        self.redis = aioredis.Redis(
            host=config['host'], port=config['port'],
            password=config['password'], ssl=True
        )

    async def save_task_state(self, task_id: str, state: dict):
        """작업 상태를 Redis에 저장"""
        await self.redis.hset(
            "active_tasks",
            task_id,
            json.dumps(state)
        )

    async def remove_task_state(self, task_id: str):
        """완료된 작업 상태를 Redis에서 제거"""
        await self.redis.hdel("active_tasks", task_id)

    async def get_all_tasks(self) -> Dict:
        """모든 활성 작업 상태 조회"""
        tasks = await self.redis.hgetall("active_tasks")
        return {
            task_id: json.loads(state)
            for task_id, state in tasks.items()
        }

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