import os
from typing import Optional
from contextlib import contextmanager
import atexit

try:
    from loguru import logger
except ImportError:
    from logging import getLogger

    logger = getLogger(__name__)
    print("please run `pip install loguru` to install loguru and see logs")

import redis

_REDIS_CONN_POOLS: dict[int, Optional[redis.Redis]] = {}


def init_redis(db: int = 0) -> None:
    global _REDIS_CONN_POOLS

    if db in _REDIS_CONN_POOLS:
        logger.info("redis is already initialized")
        return

    if os.getenv("REDIS_DB") is None or db == 0:
        logger.warning(f"REDIS_DB is not added in env, defaulting db=0")

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

        logger.debug(f"REDIS SYNC MODE - {connection_type:>{10}}")

        _REDIS_POOL_CNF = redis.ConnectionPool(**_REDIS_CONF)
        _REDIS_CONN_POOLS[db] = redis.Redis(
            unix_socket_path=os.getenv("REDIS_UNIX_SOCKET_PATH"),
            connection_pool=_REDIS_POOL_CNF,
        )

        if not _REDIS_CONN_POOLS[db].ping():
            raise Exception("can't ping redis")
    except Exception as e:
        logger.error(e)
    return


def close_redis() -> None:
    global _REDIS_CONN_POOLS

    if len(_REDIS_CONN_POOLS) > 0:
        try:
            for i in _REDIS_CONN_POOLS.values():
                logger.info(f"closing redis '{i}'")
                i.close()
        except Exception as e:
            logger.error(e)
            raise
    else:
        logger.error("redis not initialized")


atexit.register(close_redis)


@contextmanager
def lifespan():
    init_redis()
    yield
    close_redis()


def get_redis(db: int = 0) -> redis.Redis:
    global _REDIS_CONN_POOLS

    if not (db in _REDIS_CONN_POOLS):
        init_redis(db)

    return _REDIS_CONN_POOLS[db]
