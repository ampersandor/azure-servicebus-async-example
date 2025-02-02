from dataclasses import dataclass
from datetime import datetime


@dataclass
class BatchRequest:
    """Service Bus를 통해 전달되는 요청 메시지"""
    session_id: str | None
    timestamp: datetime = datetime.now()
    command: str

    @classmethod
    def from_dict(
        cls, data: dict[str, str | int | None | datetime | dict[str, str | float | int], list[str]]
    ) -> "BatchRequest":
        """딕셔너리에서 BatchRequest 객체 생성"""
        return cls(
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            command=data["command"],
        )

    def to_dict(self) -> dict[str, str | int | None | datetime | dict[str, str | float | int], list[str]]:
        """BatchRequest 객체를 딕셔너리로 변환"""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
        }

    def __str__(self) -> str:
        """문자열 표현"""
        return f"BatchRequest(session={self.session_id}, command={self.command})"