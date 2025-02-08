from azure.servicebus import ServiceBusClient, ServiceBusMessage
import uuid
import json
from datetime import datetime
import logging
import dotenv
import os

dotenv.load_dotenv()

CONNECTION_STR = os.getenv("SERVICEBUS_CONNECTION_STRING")
REQUEST_QUEUE_NAME = os.getenv("SERVICEBUS_REQUEST_QUEUE_NAME")
RESPONSE_QUEUE_NAME = os.getenv("SERVICEBUS_RESPONSE_QUEUE_NAME")

def send_batch_request():
    session_id = str(uuid.uuid4())
    logging.info(f"Starting client (Session ID: {session_id})")
    # 요청 메시지 생성
    request = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "command": "echo 'hi33'"
    }
    servicebus_client = ServiceBusClient.from_connection_string(CONNECTION_STR)
    
    with servicebus_client:
        # 요청 메시지를 보내기 위한 sender
        sender = servicebus_client.get_queue_sender(queue_name=REQUEST_QUEUE_NAME)
        
        # 응답을 받기 위한 receiver
        receiver = servicebus_client.get_queue_receiver(
            queue_name=RESPONSE_QUEUE_NAME,
            session_id=session_id,
            max_wait_time=30  # 30초 동안 응답 대기
        )
        
        with sender, receiver:
            # 메시지 전송
            message = ServiceBusMessage(
                json.dumps(request),
                session_id=session_id,
                content_type="application/json"
            )
            sender.send_messages(message)
            logging.info(f"Request sent (Session ID: {session_id})")
            
            # 응답 대기
            received_msgs = receiver.receive_messages(max_wait_time=100000)
            for msg in received_msgs:
                response = json.loads(str(msg))
                logging.info(f"Response received: {response}")
                receiver.complete_message(msg)

def main():
    # Azure 관련 로거들의 레벨 조정
    logging.getLogger("uamqp").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.servicebus").setLevel(logging.WARNING)
    logging.getLogger("azure.core").setLevel(logging.WARNING)
    
    # 애플리케이션 로그 설정
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.INFO,
        handlers=[
            logging.StreamHandler()
        ]
    )
    try:
        send_batch_request()
    except KeyboardInterrupt:
        logging.info("Client shutting down...")
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()
