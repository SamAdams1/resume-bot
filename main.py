import time
import os
import random
import requests

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine

from models.base import Base
from models.Job import Job
from models.ExcludedJob import ExcludedJob

# Database configuration
PASSWORD = os.getenv('POSTGRES_PASSWORD')
if not PASSWORD:
    raise ValueError("POSTGRES_PASSWORD environment variable not set")
DATABASE_URL = f"postgresql://postgres:{PASSWORD}@localhost:5432/apply_jobs"


# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)


TIMER = 3
RATE_LIMITED_SECONDS = 30


# Add user-agent header for Google
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

SEARXNG_URL = "http://localhost:8080"

SITES = [
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "myworkdayjobs.com",
    "myworkdaysite.com", 
    "apply.workable.com", # NEW
    "jobs.smartrecruiters.com",
    "ats.rippling.com",
    "breezy.hr",
    "recruitee.com",
    "bamboohr.com",
    "teamtailor.com",
    "applytojob.com",
    "join.com/companies/",
    "jobs.silkroad.com",
    "jobs.jobvite.com",
    "pinpointhq.com",
    "*.icims.com",
    "*.oraclecloud.com",
    "*.taleo.net",
    "*.eightfold.ai",
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

LOCATIONS = ["remote", "New Hampshire", "NH"]

EXCLUDE = ["senior", "staff", "principal", "lead", "intern", "sr", "snr"]

# Main search engines only
# Note: Google may be blocked by CAPTCHA. Try alternating engines
ENGINES = "bing,duckduckgo,brave"
# ENGINES = "google"  # Backup if others fail

def iterate_queries():
    for site in SITES:
        for role in ROLES:
            for location in LOCATIONS:
                # Build query without site: prefix (filter manually instead)
                search_query(role, location, site)
                time.sleep(TIMER)


# query example: "software engineer" (remote) site:boards.greenhouse.io"
def search_query(role: str, location: str, site: str):
    """Query local SearXNG instance and store results in database"""
    all_results = []
    
    page = 1
    MAX_PAGES = 1  # Maximum number of pages to query
    consecutive_empty_pages = 0
    MAX_EMPTY_PAGES = 3  # Stop after 3 consecutive empty pages
    
    backoff_factor = 1
    
    query = f'site:{site} "{role}" "{location}"'
    
    while page <= MAX_PAGES:
        params = {
            'q': query,
            'format': 'json',
            'engines': ENGINES,
            'pageno': page,  # Add pagination parameter
        }
        
        try:
            response = requests.get(f"{SEARXNG_URL}/search", params=params, headers=HEADERS, timeout=10)
            
            # Check for rate limiting
            if response.status_code == 429:
                print(f"Rate limited! Backing off...")
                time.sleep(RATE_LIMITED_SECONDS * backoff_factor)  # Exponential backoff
                backoff_factor *= 2
                continue
            
            # Check for forbidden or other errors
            if response.status_code != 200:
                print(f"ERROR: Got status code {response.status_code} on page {page}")
                print(f"Response: {response.text[:200]}")
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= MAX_EMPTY_PAGES:
                    print(f"Too many errors. Stopping search.")
                    break
                time.sleep(RATE_LIMITED_SECONDS * backoff_factor)
                backoff_factor *= 2
                page += 1
                continue
            
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                consecutive_empty_pages += 1
                print(f"QUERY: {query} (Page {page}, 0 results) - Empty page {consecutive_empty_pages}/{MAX_EMPTY_PAGES}")
                
                # Only stop if we hit max consecutive empty pages
                if consecutive_empty_pages >= MAX_EMPTY_PAGES:
                    print(f"Reached {MAX_EMPTY_PAGES} consecutive empty pages. Stopping search.")
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter on successful page
                all_results.extend(results)
                print(f"QUERY: {query} (Page {page}, {len(results)} results)")
            
            # Random delay between 3-8 seconds
            DELAY = random.uniform(3, 8)
            time.sleep(DELAY)
            page += 1
            
        except requests.RequestException as e:
            print(f"Error querying SearXNG on page {page}: {e}")
            consecutive_empty_pages += 1
            if consecutive_empty_pages >= MAX_EMPTY_PAGES:
                print(f"Too many errors. Stopping search.")
                break
            time.sleep(RATE_LIMITED_SECONDS * backoff_factor)
            backoff_factor *= 2
    
    if all_results:
        parse_query_results({'results': all_results}, query, location, site)
    print(f"Total results found: {len(all_results)}\n")


def extract_company_name(url):
    """Extract company name from URL, handling various formats.
    
    Tries multiple strategies:
    1. Check for company name in subdomain (before known job board domains)
    2. Check for company name in path segments
    3. Fall back to domain name or 'Unknown'
    """
    if not url:
        return 'Unknown'
    
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path_parts = [p for p in parsed.path.split('/') if p]
    
    # Known job board domain patterns to exclude
    job_board_domains = [
        'greenhouse.io', 'lever.co', 'ashbyhq.com', 'myworkdayjobs.com',
        'workable.com', 'smartrecruiters.com', 'rippling.com', 'breezy.hr',
        'recruitee.com', 'bamboohr.com', 'teamtailor.com', 'applytojob.com',
        'silkroad.com', 'jobvite.com', 'pinpointhq.com',
        'icims.com', 'oraclecloud.com', 'taleo.net', 'eightfold.ai'
    ]
    
    # Strategy 1: Extract from subdomain if domain has company-specific prefix
    for job_domain in job_board_domains:
        if job_domain in domain:
            subdomain = domain.split(f'.{job_domain}')[0]
            if subdomain and subdomain != 'jobs' and subdomain != 'job-boards' and subdomain != 'boards' and subdomain != 'apply' and subdomain != 'ats':
                return subdomain
    
    # Strategy 2: Check path for company segments (common patterns)
    if 'companies' in path_parts:
        idx = path_parts.index('companies')
        if idx + 1 < len(path_parts):
            return path_parts[idx + 1]
    
    # Strategy 3: Try common positions in path
    if len(path_parts) > 0:
        # Skip common keywords and try first meaningful segment
        skip_words = {'jobs', 'careers', 'apply', 'job', 'positions', 'openings'}
        for segment in path_parts:
            if segment.lower() not in skip_words and segment:
                return segment
    
    # Strategy 4: Fall back to domain (without known job board suffix)
    for job_domain in job_board_domains:
        if job_domain in domain:
            return domain.split(f'.{job_domain}')[0] or domain
    
    return domain or 'Unknown'


def parse_query_results(results, query, location, site):
        jobs_to_save = []
        excluded_jobs = []

        for result in results.get('results', []):
            url = result.get('url', '')
            title = result.get('title', '')
            
            # Filter out excluded terms from page title/content
            title_lower = title.lower()
            content = result.get('content', '').lower()
            
            if any(exclude.lower() in title_lower or exclude.lower() in content for exclude in EXCLUDE):
                print(f"  ✗ Excluded by filter: {title} \n   (URL: {url})")
                excluded_jobs.append({
                    'query': query,
                    'title': title,
                    'url': url,
                    'reason': f"Excluded keyword: {[e for e in EXCLUDE if e.lower() in title_lower or e.lower() in content][0]}"
                })
                continue
            
            # Filter to only include results from target site
            if site not in url:
                print(f"  ✗ Wrong site: {url} (expected {site})")
                excluded_jobs.append({
                    'query': query,
                    'title': title,
                    'url': url,
                    'reason': f"Wrong site: {site} not in URL"
                })
                continue

            
            print(f"Found: {url}")
            print(f"  Title: {title}")
            
            # Extract company name from URL using multi-strategy approach
            company = extract_company_name(url)
            
            job = Job(
                url=url,
                title=title,
                company=company,
                location=location
            )
            jobs_to_save.append(job)
        
        # Write results to database
        if jobs_to_save:
            write_results_to_database(jobs_to_save)
        if excluded_jobs:
            write_excluded_to_database(excluded_jobs)


def write_results_to_database(jobs):
    """Write job results to PostgreSQL database"""
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


def write_excluded_to_database(excluded_jobs):
    """Write excluded job results to PostgreSQL database"""
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


# iterate_queries()
for site in SITES:
    search_query("software engineer", "Remote", site)
# search_query("software engineer", "Remote", "boards.greenhouse.io")

