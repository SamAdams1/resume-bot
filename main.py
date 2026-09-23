# query example: "software engineer" (remote) site:boards.greenhouse.io"
import time
from datetime import datetime
import os

import requests
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/apply_jobs"


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
ENGINES = "bing,brave,google,duckduckgo"

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
    """Query local SearXNG instance"""
    params = {
        'q': query,
        'format': 'json',
        # 'engines': ENGINES,  # Filter to main search engines
    }
    
    try:
        response = requests.get(f"{SEARXNG_URL}/search", params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Debug: print response
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:200]}")
        print(f"Query: {query}")
        
        results = response.json()
        # print(f"Results: {results}")
        # return results
        
        for result in results.get('results', []):
            url = result.get('url', '')
            
            # Filter out excluded terms from page title/content
            title = result.get('title', '').lower()
            content = result.get('content', '').lower()
            
            if any(exclude.lower() in title or exclude.lower() in content for exclude in EXCLUDE):
                continue
            
            print(f"Found: {url}")
            print(f"  Title: {result.get('title')}")
            
    except requests.RequestException as e:
        print(f"Error querying SearXNG: {e}")

def write_results_to_database(results):


iterate_queries()
# search_query('"software engineer" "remote" site:boards.greenhouse.io')