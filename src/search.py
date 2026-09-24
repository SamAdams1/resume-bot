"""Search module for querying SearXNG and handling results."""

import requests
import time
import random

from config import (
    ENGINES, HEADERS, SEARXNG_URL, RATE_LIMITED_SECONDS
)
from parse_jobs import parse_query_results


def search_query(role: str, location: str, site: str) -> int:
    """Query local SearXNG instance and store results in database.
    
    Args:
        role: Job role to search for
        location: Job location
        site: Target job board domain
        
    Returns:
        Number of results found
    """
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
    
    return len(all_results)

