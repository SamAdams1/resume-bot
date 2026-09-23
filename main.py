# query example: "software engineer" (remote) site:boards.greenhouse.io"
import time
from datetime import datetime
import os

import requests
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
load_dotenv()

# Database configuration
PASSWORD = os.getenv('POSTGRES_PASSWORD')
if not PASSWORD:
    raise ValueError("POSTGRES_PASSWORD environment variable not set")
DATABASE_URL = f"postgresql://postgres:{PASSWORD}@localhost:5432/apply_jobs"


# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define Job model
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    applied = Column(Boolean, default=False), 
    match_percent = Column(Integer, nullable=True)
    date_found = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Job(url='{self.url}', title='{self.title}', company='{self.company}')>"

# Create tables
Base.metadata.create_all(engine)

rate_limit_seconds = 1

# Add user-agent header for Google
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

SEARXNG_URL = "http://localhost:8080"

SITES = [
    "boards.greenhouse.io",
    # "jobs.lever.co",
    # "jobs.ashbyhq.com",
    # "site:myworkdayjobs.com"
]

ROLES = [
    'software engineer',
    'backend engineer',
    'frontend engineer',
    'full stack engineer',
    'web developer',
    'software developer',
    'application developer',
    'application engineer'
]

INCLUDE = ["remote", "New Hampshire", "NH"]

EXCLUDE = ["senior", "staff", "principal", "lead", "intern", "sr"]

# Main search engines only
ENGINES = "bing,brave,duckduckgo"#,google"

def iterate_queries():
    for site in SITES:
        for role in ROLES:
            for include in INCLUDE:
                for exclude in EXCLUDE:
                    # Build query without site: prefix (filter manually instead)
                    query = f'"{role}" "{include}" -"{exclude}" site:{site}'
                    search_query(query)
                    time.sleep(rate_limit_seconds)
  
def search_query(query):
    """Query local SearXNG instance and store results in database"""
    params = {
        'q': query,
        'format': 'json',
        'engines': ENGINES,  
    }
    
    try:
        response = requests.get(f"{SEARXNG_URL}/search", params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Debug: print response
        print(f"Response status: {response.status_code}")
        print(f"Query: {query}")
        
        parse_query_results(response.json())
            
    except requests.RequestException as e:
        print(f"Error querying SearXNG: {e}")

def parse_query_results(results):
        jobs_to_save = []

        for result in results.get('results', []):
            url = result.get('url', '')
            
            # Filter out excluded terms from page title/content
            title = result.get('title', '').lower()
            content = result.get('content', '').lower()
            
            if any(exclude.lower() in title or exclude.lower() in content for exclude in EXCLUDE):
                continue
            
            print(f"Found: {url}")
            print(f"  Title: {result.get('title')}")
            
            # Extract company name from URL (simplified)
            company = url.split('/')[3].replace('www.', '') if url else 'Unknown'
            
            job = Job(
                url=url,
                title=result.get('title', ''),
                company=company
            )
            jobs_to_save.append(job)
        
        # Write results to database
        if jobs_to_save:
            write_results_to_database(jobs_to_save)

def write_results_to_database(jobs):
    """Write job results to PostgreSQL database"""
    session = Session()
    try:
        for job in jobs:
            # Check if job already exists (by URL)
            existing = session.query(Job).filter(Job.url == job.url).first()
            if not existing:
                session.add(job)
                print(f"  ✓ Saved to DB: {job.title}")
            else:
                print(f"  ↻ Already in DB: {job.title}")
        
        session.commit()
        print(f"Successfully saved {len([j for j in jobs if not session.query(Job).filter(Job.url == j.url).first()])} new jobs")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()


# iterate_queries()
search_query('"software engineer" "remote" site:boards.greenhouse.io')