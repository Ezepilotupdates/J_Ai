# app/memory.py
import aioredis
import asyncpg
import os
import json

REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

class Memory:
    def __init__(self, redis_url=None):
        self.redis_url = redis_url or REDIS_URL
        self.redis = None
        self.pg_pool = None

    async def connect(self):
        if self.redis_url:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
        if DATABASE_URL:
            self.pg_pool = await asyncpg.create_pool(DATABASE_URL)

    async def close(self):
        if self.redis:
            await self.redis.close()
        if self.pg_pool:
            await self.pg_pool.close()

    async def append_message(self, chat_id, role, content):
        if not self.redis:
            return
        key = f"hist:{chat_id}"
        await self.redis.rpush(key, json.dumps({"role": role, "content": content}))
        await self.redis.ltrim(key, -40, -1)
        await self.redis.expire(key, 7*24*3600)

    async def get_history(self, chat_id):
        if not self.redis:
            return []
        items = await self.redis.lrange(f"hist:{chat_id}", 0, -1)
        return [json.loads(i) for i in items]

    async def clear_chat(self, chat_id):
        if self.redis:
            await self.redis.delete(f"hist:{chat_id}")

    async def get_all_users(self):
        if not self.pg_pool:
            return []
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT id FROM users")
            return rows