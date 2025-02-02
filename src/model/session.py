from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.now())
    results = relationship("Result", back_populates="session")