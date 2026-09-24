"""Main orchestration module for job search application."""

import time

from config import TIMER, SITES, ROLES, LOCATIONS
from search import search_query

# Counter tracking
total_jobs_found = 0
total_valid_jobs = 0
total_jobs_excluded = 0


def iterate_queries():
    """Iterate through all site/role/location combinations."""
    global total_jobs_found, total_valid_jobs, total_jobs_excluded
    
    for site in SITES:
        for role in ROLES:
            for location in LOCATIONS:
                # Execute search
                results_found = search_query(role, location, site)
                total_jobs_found += results_found
                time.sleep(TIMER)


if __name__ == "__main__":
    # Run searches for current configuration
    
    for site in SITES:
        results_found = search_query("software engineer", "Remote", site)
        total_jobs_found += results_found
    
    # Print final summary
    print("\n" + "="*60)
    print("JOB SEARCH SUMMARY")
    print("="*60)
    print(f"Total jobs found: {total_jobs_found}")
    print(f"Total valid jobs saved: {total_valid_jobs}")
    print(f"Total jobs excluded: {total_jobs_excluded}")
    print("="*60)

