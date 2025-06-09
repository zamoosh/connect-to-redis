import os
from dotenv import load_dotenv

load_dotenv()

REDIS_POP_COUNT = int(os.getenv("REDIS_POP_COUNT", 100))
REDIS_KEY_EXPIRE = int(os.getenv("REDIS_KEY_EXPIRE", 60))
