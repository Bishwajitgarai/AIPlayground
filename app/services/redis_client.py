import redis
from app.core.config import settings

redis_client=redis.Redis(
        host=settings.REDIS_HOST,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        port=settings.REDIS_PORT
        )