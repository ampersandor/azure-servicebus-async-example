from azure.servicebus import ServiceBusClient, ServiceBusMessage
import uuid
import time
import dotenv
import os
dotenv.load_dotenv()

CONNECTION_STR = os.getenv("SERVICEBUS_CONNECTION_STRING")
REQUEST_QUEUE_NAME = os.getenv("SERVICEBUS_REQUEST_QUEUE_NAME")
RESPONSE_QUEUE_NAME = os.getenv("SERVICEBUS_RESPONSE_QUEUE_NAME")

def client_main():
    print(f"요청 큐: {REQUEST_QUEUE_NAME}")
    print(f"응답 큐: {RESPONSE_QUEUE_NAME}")
    session_id = str(uuid.uuid4())
    print(f"클라이언트 시작 (세션 ID: {session_id})")
    
    servicebus_client = ServiceBusClient.from_connection_string(CONNECTION_STR)
    
    with servicebus_client:
        # 요청 메시지를 보내기 위한 sender
        sender = servicebus_client.get_queue_sender(queue_name=REQUEST_QUEUE_NAME)
        
        # 응답을 받기 위한 receiver
        receiver = servicebus_client.get_queue_receiver(
            queue_name=RESPONSE_QUEUE_NAME,
            session_id=session_id,
            max_wait_time=100000
        )
        
        with sender, receiver:
            # 메시지 전송
            message = ServiceBusMessage(
                f"안녕하세요? 저는 {session_id}번 클라이언트에요!",
                session_id=session_id
            )
            sender.send_messages(message)
            print(f"메시지 전송 완료 (세션 ID: {session_id})")
            
            # 응답 대기
            received_msgs = receiver.receive_messages(max_wait_time=10)
            for msg in received_msgs:
                print(f"서버로부터 응답 받음: {str(msg)}")
                receiver.complete_message(msg)

if __name__ == "__main__":
    client_main()
