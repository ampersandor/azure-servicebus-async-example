from dotenv import load_dotenv
import os
load_dotenv()


class ServiceBusConfig:
    connection_str: str = os.getenv("SERVICEBUS_CONNECTION_STRING")
    request_queue: str = os.getenv("SERVICEBUS_REQUEST_QUEUE_NAME")
    response_queue: str = os.getenv("SERVICEBUS_RESPONSE_QUEUE_NAME")

    
