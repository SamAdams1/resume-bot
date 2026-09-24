from models.base import Base
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer 

# Define ExcludedJob model
class ExcludedJob(Base):
    __tablename__ = "excluded_jobs"
    
    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    reason = Column(String, nullable=False)
    date_found = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ExcludedJob(url='{self.url}', reason='{self.reason}')>"
