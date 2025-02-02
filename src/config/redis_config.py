from dotenv import load_dotenv
import os
load_dotenv()


class RedisConfig:
    host: str = os.getenv("REDIS_URL")
    port: int = os.getenv("REDIS_PORT")
    password: str = os.getenv("REDIS_PASSWORD")
    db: int = os.getenv("REDIS_DB")

    
