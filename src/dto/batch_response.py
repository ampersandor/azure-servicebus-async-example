from dataclasses import dataclass
from datetime import datetime


@dataclass
class BatchResponse:
    """Batch 작업 결과 응답 메시지"""
    session_id: str
    result_paths: list[str]  # Blob storage의 결과 파일 경로
    status: str = "completed"  # completed, error
    error_message: str | None = None
    timestamp: datetime = datetime.now()

    @classmethod
    def from_dict(cls, data: dict[str, str | None | datetime]) -> "BatchResponse":
        """딕셔너리에서 BatchResponse 객체 생성"""
        return cls(
            session_id=data["session_id"],
            result_paths=data["result_paths"],
            status=data.get("status", "completed"),
            error_message=data.get("error_message"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )

    def to_dict(self) -> dict[str, str | None, datetime]:
        """BatchResponse 객체를 딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "result_paths": self.result_paths,
            "status": self.status,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        """문자열 표현"""
        return f"BatchResponse(session={self.session_id}, status={self.status}, path={self.result_paths})"
