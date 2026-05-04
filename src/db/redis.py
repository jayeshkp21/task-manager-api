from redis import asyncio as aioredis
from src.config import Config
import logging

# Setup a simple logger to see what's happening
logger = logging.getLogger("uvicorn.error")

JTI_EXPIRY = 3600  #1 hour

token_blocklist = aioredis.StrictRedis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=0
)

async def add_jti_to_blocklist(jti:str) -> None:
    try:
        await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY)
    except Exception as e:
        logger.warning(f"Could not add to Redis: {e}")
    
async def token_in_blocklist(jti:str) -> bool:
    try:
        res = await token_blocklist.get(jti)
        return res is not None
    except Exception as e:
        # If Redis is down, we assume the token isn't blocked so the app doesn't crash
        logger.warning(f"Redis connection failed, skipping blocklist check: {e}")
        return False