from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Result(Base):
    __tablename__ = "results"

    result_id = Column(String, primary_key=True)
    command = Column(String)
    result_path = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    session_id = Column(String, ForeignKey("sessions.session_id"))
    session = relationship("Session", back_populates="results")