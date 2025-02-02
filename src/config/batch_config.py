from dotenv import load_dotenv
import os
load_dotenv()


class BatchConfig:
    account_name: str = os.getenv("BATCH_ACCOUNT_NAME")
    account_key: str = os.getenv("BATCH_ACCOUNT_KEY")
    account_url: str = os.getenv("BATCH_ACCOUNT_URL")
    pool_id: str = os.getenv("POOL_ID")

    
