from azure.servicebus import ServiceBusClient, ServiceBusMessage, NEXT_AVAILABLE_SESSION
from azure.servicebus.exceptions import OperationTimeoutError
import dotenv
import os
import time
import concurrent.futures
from typing import List

# .env 파일 로드
dotenv.load_dotenv()

CONNECTION_STR = os.getenv("SERVICEBUS_CONNECTION_STRING")
REQUEST_QUEUE_NAME = os.getenv("SERVICEBUS_REQUEST_QUEUE_NAME")
RESPONSE_QUEUE_NAME = os.getenv("SERVICEBUS_RESPONSE_QUEUE_NAME")


def process_message(message, session_id):
    # 메시지 처리 로직
    print(f"받은 메시지: {message}")
    # 처리된 결과를 반환
    return f"안녕하세요! {session_id}번 클라이언트님 전 서버에요 반가워요!"

def handle_session(servicebus_client, sender, queue_name):
    try:
        with servicebus_client.get_queue_receiver(
            queue_name=queue_name,
            session_id=NEXT_AVAILABLE_SESSION,
            max_wait_time=5
        ) as receiver:
            print(f"세션 연결됨: {receiver.session.session_id}")
            receiver.session.set_state("OPEN")
            
            for message in receiver:
                try:
                    print(f"\n새 메시지 수신: {message.session_id} - {str(message)}")
                    
                    result = process_message(str(message), message.session_id)
                    response = ServiceBusMessage(result, session_id=message.session_id)
                    sender.send_messages(response)
                    
                    receiver.complete_message(message)
                    print(f"응답 전송 완료: {result}")
                    
                except Exception as msg_error:
                    print(f"메시지 처리 중 에러: {str(msg_error)}")
                    receiver.abandon_message(message)
            
            receiver.session.set_state("CLOSED")
            
    except OperationTimeoutError:
        print("사용 가능한 세션 없음")
    except Exception as e:
        print(f"세션 처리 중 에러: {str(e)}")

def server_main():
    print(f"연결 문자열: {CONNECTION_STR[:50]}...")
    
    servicebus_client = ServiceBusClient.from_connection_string(CONNECTION_STR)
    concurrent_receivers = 5
    
    with servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=RESPONSE_QUEUE_NAME)
        
        # ThreadPoolExecutor를 while 루프 밖에 생성
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_receivers) as thread_pool:
            while True:
                try:
                    # 현재 실행 중인 future의 개수 확인
                    running_futures = list(filter(lambda x: not x.done(), futures)) if 'futures' in locals() else []
                    
                    # 추가로 필요한 스레드 수 계산
                    needed_threads = concurrent_receivers - len(running_futures)
                    
                    # 필요한 만큼만 새로운 스레드 생성
                    if needed_threads > 0:
                        new_futures = [
                            thread_pool.submit(
                                handle_session, 
                                servicebus_client, 
                                sender, 
                                REQUEST_QUEUE_NAME
                            )
                            for _ in range(needed_threads)
                        ]
                        
                        # 실행 중인 futures 리스트 업데이트
                        futures = running_futures + new_futures
                    
                    # 잠시 대기 (과도한 CPU 사용 방지)
                    time.sleep(0.1)
                        
                except Exception as e:
                    print(f"에러 발생: {str(e)}")
                    time.sleep(1)

if __name__ == "__main__":
    server_main()
