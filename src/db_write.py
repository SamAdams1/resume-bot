
"""Database write operations for job results."""

import sys
import os
from pathlib import Path

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine

from config import DATABASE_URL
from models.base import Base
from models.Job import Job
from models.ExcludedJob import ExcludedJob

# Create engine and session (initialize once)
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)

# Counter tracking (will be incremented by main.py)
total_valid_jobs_saved = 0
total_jobs_excluded = 0


def write_results_to_database(jobs):
    """Write job results to PostgreSQL database.
    
    Args:
        jobs: List of Job objects to save
        
    Returns:
        Number of jobs successfully saved
    """
    session = Session()
    num_jobs_saved = 0
    try:
        for job in jobs:
            # Check if job already exists (by URL)
            existing = session.query(Job).filter(Job.url == job.url).first()
            if not existing:
                session.add(job)
                print(f"  ✓ Saved to DB: {job.title}")
                num_jobs_saved += 1
            else:
                print(f"  ↻ Already in DB: {job.title}")
        
        session.commit()
        print(f"Successfully saved {num_jobs_saved} new jobs")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()
    
    return num_jobs_saved


def write_excluded_to_database(excluded_jobs):
    """Write excluded job results to PostgreSQL database.
    
    Args:
        excluded_jobs: List of excluded job data dicts
        
    Returns:
        Number of exclusions successfully logged
    """
    session = Session()
    num_excluded_saved = 0
    try:
        for job_data in excluded_jobs:
            # Check if this exclusion already exists
            existing = session.query(ExcludedJob).filter(ExcludedJob.url == job_data['url']).first()
            if not existing:
                excluded_job = ExcludedJob(
                    query=job_data['query'],
                    title=job_data['title'],
                    url=job_data['url'],
                    reason=job_data['reason']
                )
                session.add(excluded_job)
                num_excluded_saved += 1
        
        session.commit()
        if num_excluded_saved > 0:
            print(f"  Logged {num_excluded_saved} excluded jobs")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error writing excluded jobs: {e}")
    finally:
        session.close()
    
    return num_excluded_saved
