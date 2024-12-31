from azure.servicebus import ServiceBusClient, ServiceBusMessage, NEXT_AVAILABLE_SESSION
from azure.servicebus.exceptions import OperationTimeoutError
import dotenv
import os
import time

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

def server_main():
    print(f"연결 문자열: {CONNECTION_STR[:50]}...")  # 보안을 위해 일부만 출력
    print(f"요청 큐: {REQUEST_QUEUE_NAME}")
    print(f"응답 큐: {RESPONSE_QUEUE_NAME}")
    
    servicebus_client = ServiceBusClient.from_connection_string(CONNECTION_STR)
    
    print("서버가 시작되었습니다. 메시지 대기 중...")
    
    with servicebus_client:
        # 응답 sender 생성
        sender = servicebus_client.get_queue_sender(queue_name=RESPONSE_QUEUE_NAME)
        
        while True:
            try:
                print("\n세션 대기 중...")
                
                # 다음 사용 가능한 세션으로 수신자 생성
                with servicebus_client.get_queue_receiver(
                    queue_name=REQUEST_QUEUE_NAME,
                    session_id=NEXT_AVAILABLE_SESSION,
                    max_wait_time=5
                ) as receiver:
                    print(f"세션 연결됨: {receiver.session.session_id}")
                    
                    # 세션 상태 설정
                    receiver.session.set_state("OPEN")
                    
                    # 메시지 수신 및 처리
                    for message in receiver:
                        try:
                            print("\n새 메시지 수신:")
                            print(f"세션 ID: {message.session_id}")
                            print(f"시퀀스 번호: {message.sequence_number}")
                            print(f"내용: {str(message)}")
                            
                            # 메시지 처리
                            result = process_message(str(message), message.session_id)
                            
                            # 응답 전송
                            response = ServiceBusMessage(
                                result,
                                session_id=message.session_id
                            )
                            sender.send_messages(response)
                            print(f"응답 전송 완료: {result}")
                            
                            # 메시지 완료 처리
                            receiver.complete_message(message)
                            
                        except Exception as msg_error:
                            print(f"메시지 처리 중 에러: {str(msg_error)}")
                            receiver.abandon_message(message)
                    
                    # 세션 종료
                    receiver.session.set_state("CLOSED")
                    
            except OperationTimeoutError:
                print("사용 가능한 세션 없음")
                time.sleep(1)
                continue
                
            except Exception as e:
                print(f"에러 발생: {str(e)}")
                time.sleep(1)

if __name__ == "__main__":
    server_main()
