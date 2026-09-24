# Define Job model
from models.base import Base
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, Boolean

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    location = Column(String, nullable=True)
    url = Column(String, unique=True, nullable=False)
    company = Column(String, nullable=True)
    applied = Column(Boolean, default=False)
    match_percent = Column(Integer, nullable=True)
    emailed_hiring_manager = Column(Boolean, default=False)
    date_found = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Job(url='{self.url}', title='{self.title}', company='{self.company}')>"
