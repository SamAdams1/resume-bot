
"""Job parsing module for filtering and extracting job information."""

import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import EXCLUDE
from models.Job import Job
from db_write import write_results_to_database, write_excluded_to_database


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
    """Parse search results, filter by criteria, and save to database.
    
    Args:
        results: Dict with 'results' key containing search results
        query: Original search query string
        location: Job location filter
        site: Target job board site
        
    Returns:
        Tuple of (valid_jobs_count, excluded_jobs_count)
    """
    jobs_to_save = []
    excluded_jobs = []

    for result in results.get('results', []):
        url = result.get('url', '')
        title = result.get('title', '')
        
        # Filter out excluded terms from page title/content
        title_lower = title.lower()
        content = result.get('content', '').lower()
        
        if any(exclude.lower() in title_lower or exclude.lower() in content for exclude in EXCLUDE):
            excluded_keyword = [e for e in EXCLUDE if e.lower() in title_lower or e.lower() in content][0]
            print(f"    ✗ Excluded keyword '{excluded_keyword}': {title} \n   (URL: {url})")
            excluded_jobs.append({
                'query': query,
                'title': title,
                'url': url,
                'reason': f"Excluded keyword: {excluded_keyword}"
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
        
        # Extract company name from URL using multi-strategy approach
        company = extract_company_name(url)
        
        job = Job(
            url=url,
            title=title,
            company=company,
            location=location
        )
        jobs_to_save.append(job)
    
    # Write results to database and track counts
    valid_count = 0
    excluded_count = 0
    
    if jobs_to_save:
        valid_count = write_results_to_database(jobs_to_save)
    if excluded_jobs:
        excluded_count = write_excluded_to_database(excluded_jobs)
    
    return valid_count, excluded_count

