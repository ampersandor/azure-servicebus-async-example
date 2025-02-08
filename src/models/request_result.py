from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from src.models.base import Base

# Association table
request_result = Table(
    'request_result',
    Base.metadata,
    Column('request_id', String, ForeignKey('requests.request_id')),
    Column('result_id', String, ForeignKey('results.result_id')),
    Column('created_at', DateTime)
) 