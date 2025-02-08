from dotenv import load_dotenv
import os
load_dotenv()

class BlobConfig:
    BLOB_URL = os.getenv("BLOB_URL")