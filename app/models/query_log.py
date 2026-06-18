from sqlalchemy import Column,Integer,String,Float,DateTime
from app.database import Base
from sqlalchemy.sql import func

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer,primary_key=True,index=True)
    question = Column(String,index=True)
    answer = Column(String,index=True)
    response_time = Column(Float)
    answer_found = Column(Integer)
    created_at = Column(DateTime(timezone=True),
    server_default=func.now())
