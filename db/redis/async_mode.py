import os
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

try:
    from loguru import logger
except ImportError:
    from logging import getLogger

    logger = getLogger(__name__)
    print("please run `pip install loguru` to install loguru and see logs")

import redis.asyncio as redis

_REDIS_CONN_POOLS: dict[int, Optional[redis.Redis]] = {}


async def init_redis(db: int = 0) -> None:
    global _REDIS_CONN_POOLS

    if db in _REDIS_CONN_POOLS:
        logger.info("redis is already initialized")
        return

    if os.getenv("REDIS_DB") is None and db == 0:
        logger.warning(f"REDIS_DB is not added in env, defaulting db=0")

    while True:
        try:
            _REDIS_CONF = {
                "db": db,
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
            _REDIS_CONN_POOLS[db] = redis.Redis(
                unix_socket_path=os.getenv("REDIS_UNIX_SOCKET_PATH"),
                connection_pool=_REDIS_POOL_CNF,
            )

            if not await _REDIS_CONN_POOLS[db].ping():
                raise Exception("can't ping redis")

            break
        except redis.ConnectionError:
            logger.error("error connecting to redis, retrying in 10 secs.")
            await asyncio.sleep(10)
            continue
        except Exception as e:
            logger.error(f"unknown err: {e}")
            break
    return


async def close_redis() -> None:
    global _REDIS_CONN_POOLS

    if len(_REDIS_CONN_POOLS) > 0:
        try:
            for i in _REDIS_CONN_POOLS.values():
                if i is not None:
                    logger.info(f"closing redis '{i}'")
                    await i.aclose()
        except Exception as e:
            logger.error(e)
            raise
    else:
        logger.error("redis not initialized")


async def re_connect(timeout: int = 30, sleep_time: int = 5) -> None:
    """
    This is a blocking function which tries to connect to redis.
    If timeout reaches, we break, whatever we've connected or not.

    :param timeout: Indicates how long to wait for to connect to redis
    :type timeout: int
    :param sleep_time: The slipage time we wait and for each sleep, we minus timeout and sleep
    :type sleep_time: int
    :return: nothing
    :rtype: None
    """

    global _REDIS_CONN_POOLS

    if len(_REDIS_CONN_POOLS) == 0:
        logger.warning(f"redis not initialized")
        return

    if timeout > 50:
        logger.warning(f"timeout is big, defaulting to 30")
        timeout = 30

    if sleep_time > timeout:
        logger.warning(f"sleep time {sleep_time} > {timeout}, defaulting to 5")
        sleep_time = 5

    connected: bool = False
    while True:
        try:
            if timeout <= 0:
                break

            key: Optional[int | str] = None
            for i in _REDIS_CONN_POOLS.keys():
                key = i
                break
            await _REDIS_CONN_POOLS[key].ping()
            connected = True
            break
        except redis.ConnectionError:
            logger.info(f"retrying in {sleep_time} seconds")
            await asyncio.sleep(sleep_time)
            timeout -= sleep_time

    if connected:
        logger.success("connected")
    else:
        logger.warning(f"could not connect to redis")

    return


@asynccontextmanager
async def lifespan():
    await init_redis()
    yield
    await close_redis()


async def get_redis(db: int = 0) -> redis.Redis:
    global _REDIS_CONN_POOLS

    if db not in _REDIS_CONN_POOLS:
        await init_redis(db)

    return _REDIS_CONN_POOLS[db]
