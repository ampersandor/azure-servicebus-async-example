from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base
from src.models.request_result import request_result

class Request(Base):
    """ServiceBus를 통해 들어오는 작업 요청"""
    __tablename__ = "requests"

    request_id = Column(String, primary_key=True)  # ServiceBus session_id
    command = Column(String, nullable=False)  # 실행할 명령어
    created_at = Column(DateTime, default=datetime.now())
    results = relationship(
        "Result",
        secondary=request_result,
        back_populates="requests"
    ) 