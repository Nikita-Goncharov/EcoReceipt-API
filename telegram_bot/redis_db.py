import os

import redis.asyncio as redis
from dotenv import load_dotenv


load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PORT = int(REDIS_PORT) if REDIS_PORT is not None else 6379

redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


async def save_user_auth_status(user_id: int, is_logged_in: bool = False, token: str = ""):
    user_key = f"user: {str(user_id)}"
    await redis_db.hset(user_key, mapping={
        "user_id": user_id,
        "token": token,
        "is_logged_in": int(is_logged_in)
    })


async def get_user_auth_status(user_id: str) -> dict:
    user_key = f"user: {user_id}"
    data = await redis_db.hgetall(user_key)
    if data:
        return {
            "user_id": user_id,
            "token": data.get(b"token").decode(),
            "is_logged_in": int(data.get(b"is_logged_in").decode())
        }

    return {
            "user_id": user_id,
            "token": "",
            "is_logged_in": 0  # Repr of False in redis
        }
