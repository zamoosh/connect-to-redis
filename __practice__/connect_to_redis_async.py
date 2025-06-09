import asyncio
from dotenv import load_dotenv

load_dotenv()

from db.redis.async_mode import get_redis, close_redis


async def main():
    r = await get_redis()
    await r.set("name", "ali")

    name = await r.get("name")
    print(f"name is '{name}'")

    return


async def lifespan():
    try:
        await main()
    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(lifespan())
