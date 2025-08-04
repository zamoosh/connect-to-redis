# Redis Connection Utility (Sync & Async)

A simple utility library for managing **Redis connections** in both **asynchronous** and **synchronous** Python applications, using support for both **TCP** and **Unix Socket** connections. Includes automatic lifecycle management, context management support, and `loguru`-based logging.

---

## 🔧 Features

* Async and Sync Redis connection management
* Environment-variable configuration
* Loguru-based logging (fallback to `logging`)
* Graceful connection closing
* Supports TCP and Unix socket Redis connections
* Context manager (`lifespan`) for scoped Redis usage
* Runtime support for **multiple Redis databases**

---

## 📦 Installation

```bash
pip install redis loguru python-dotenv
```

---

## 🥪 Environment Variables

Set these in your `.env` file or system environment depending on your connection type:

### ✨ Common

```env
# REDIS_DB=0             # ❌ Deprecated — use `get_redis(db=...)` or `init_redis(db=...)` instead
REDIS_PASS=your_password # Password for authentication
REDIS_USERNAME=          # Optional username (used in Redis ACL setups)
REDIS_MAX_CONNECTIONS=50 # Max number of Redis connections in the pool
```

### 🛎️ For TCP connection

```env
REDIS_HOST=127.0.0.1      # Redis server hostname or IP
REDIS_PORT=6379           # Redis server port number
```

### 📼 For Unix Socket connection

```env
REDIS_UNIX_SOCKET_PATH=/path/to/redis.sock  # Full path to Redis UNIX socket file
```

> **Note:** The library will automatically choose between TCP and Unix Socket connection based on the presence of `REDIS_HOST` and `REDIS_PORT`. If those are not set, it defaults to Unix socket.

---

## 🗒 Usage: All code below are available in "_\_practice__" module

## 🚀 Async Usage

### 1. Scoped Connection (using `lifespan`)

```py
import asyncio
from dotenv import load_dotenv
load_dotenv()

from db.redis.async_mode import get_redis, lifespan

async def main():
    async with lifespan():
        r = await get_redis()
        await r.set("name", "ali")
        print(f"name is '{await r.get('name')}'")

asyncio.run(main())
```

### 2. Full Program Lifecycle (manual close)

```py
import asyncio
from dotenv import load_dotenv
load_dotenv()

from db.redis.async_mode import get_redis, close_redis

async def main():
    r = await get_redis()
    await r.set("name", "ali")
    print(f"name is '{await r.get('name')}'")

async def lifespan():
    try:
        await main()
    finally:
        await close_redis()

asyncio.run(lifespan())
```

### 3. Using Multiple Databases at Runtime (NEW ⚡)

You can dynamically connect to different Redis databases by passing the `db` argument:

```py
from db.redis.async_mode import get_redis

async def use_multiple_dbs():
    r0 = await get_redis(db=0)
    await r0.set("key:0", "value in db 0")

    r1 = await get_redis(db=1)
    await r1.set("key:1", "value in db 1")

    print(await r0.get("key:0"))  # Output: value in db 0
    print(await r1.get("key:1"))  # Output: value in db 1
```

---

## 🐢 Sync Usage

Automatically closes Redis connection at the end of your program using `atexit`.

```py
from dotenv import load_dotenv
load_dotenv()

from db.redis.sync_mode import get_redis

def main():
    r = get_redis()
    r.set("name", "ali")
    print(f"name is '{r.get('name')}'")

if __name__ == "__main__":
    main()
```

---

## 📚 API Reference

### Async Mode

```py
from db.redis.async_mode import init_redis, close_redis, get_redis, lifespan
```

* `await init_redis(db=0)` – Initializes connection pool for given database
* `await close_redis()` – Closes all connection pools
* `await get_redis(db=0)` – Returns a Redis client for given database
* `lifespan()` – Async context manager for scoped connection

### Sync Mode

```py
from db.redis.sync_mode import init_redis, close_redis, get_redis, lifespan
```

* `init_redis(db=0)` – Initializes connection pool for given database
* `close_redis()` – Closes all connection pools (also registered to `atexit`)
* `get_redis(db=0)` – Returns a Redis client for given database
* `lifespan()` – Context manager for scoped connection

---

## 🐞 Logging

This library uses [`loguru`](https://github.com/Delgan/loguru) for better logging experience. If not installed, it falls back to the default Python `logging`.

To enable full logging:

```bash
pip install loguru
```

---

## 📝 License

MIT License — free to use and modify.
