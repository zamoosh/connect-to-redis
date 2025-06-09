import os
from typing import Optional
from contextlib import asynccontextmanager

try:
    from loguru import logger
except ImportError:
    from logging import getLogger

    logger = getLogger(__name__)
    print("please run `pip install loguru` to install loguru and see logs")

import redis.asyncio as redis

_REDIS_CONN_POOL: Optional[redis.Redis] = None


async def init_redis() -> None:
    global _REDIS_CONN_POOL

    if _REDIS_CONN_POOL is not None:
        logger.info("redis is already initialized")
        return

    try:
        _REDIS_CONF = {
            "db": int(os.getenv("REDIS_DB", 0)),
            "password": os.getenv("REDIS_PASS", ""),
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
            "decode_responses": True,
        }

        connection_type = "TCP"
        if os.getenv("REDIS_HOST") is not None and os.getenv("REDIS_PORT") is not None:
            _REDIS_CONF.update(
                {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": int(os.getenv("REDIS_PORT", "6379")),
                }
            )
        else:
            connection_type = "UNIXSOCKET"

        logger.debug(f"REDIS ASYNC MODE - {connection_type:>{10}}")

        _REDIS_POOL_CNF = redis.ConnectionPool(**_REDIS_CONF)
        _REDIS_CONN_POOL = redis.Redis(
            unix_socket_path=os.getenv("REDIS_UNIX_SOCKET_PATH"), connection_pool=_REDIS_POOL_CNF
        )

        if not await _REDIS_CONN_POOL.ping():
            raise Exception("can't ping redis")
    except Exception as e:
        logger.error(e)
    return


async def close_redis() -> None:
    global _REDIS_CONN_POOL

    if _REDIS_CONN_POOL is not None:
        try:
            logger.info("closing redis")
            await _REDIS_CONN_POOL.aclose()
        except Exception as e:
            logger.error(e)
            raise
    else:
        logger.error("redis not initialized")


@asynccontextmanager
async def lifespan():
    await init_redis()
    yield
    await close_redis()


async def get_redis() -> redis.Redis:
    global _REDIS_CONN_POOL

    if _REDIS_CONN_POOL is None:
        await init_redis()

    return _REDIS_CONN_POOL
