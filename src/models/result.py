from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from src.models.base import Base
from src.models.request_result import request_result

class ResultStatus(enum.Enum):
    """작업 상태"""
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'

class Result(Base):
    """작업 실행 결과"""
    __tablename__ = "results"

    result_id = Column(String, primary_key=True)
    result_path = Column(String, nullable=True)  # 초기에는 NULL 가능
    status = Column(
        Enum(ResultStatus, name='resultstatus', create_constraint=True, native_enum=True),  # PostgreSQL enum 사용
        default=ResultStatus.PENDING,
        nullable=False
    )  # 작업 상태
    created_at = Column(DateTime, default=datetime.now())
    requests = relationship(
        "Request",
        secondary=request_result,
        back_populates="results"
    )

    def update_status(self, new_status: ResultStatus) -> None:
        """작업 상태 업데이트"""
        self.status = new_status