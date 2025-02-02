from dotenv import load_dotenv
import os
load_dotenv()


class PSQLConfig:
    host: str = os.getenv("PGSQL_URL")
    user: str = os.getenv("PGSQL_USER")
    password: str = os.getenv("PGSQL_PASSWORD")
    database: str = os.getenv("PGSQL_DATABASE")
    port: int = os.getenv("PGSQL_PORT")

    
