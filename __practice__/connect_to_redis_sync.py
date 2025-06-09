from dotenv import load_dotenv

load_dotenv()

from db.redis.sync_mode import get_redis


def main():
    r = get_redis()
    r.set("name", "ali")

    name = r.get("name")
    print(f"name is '{name}'")

    return


if __name__ == "__main__":
    main()
