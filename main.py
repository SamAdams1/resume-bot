# query example: "software engineer" (remote) site:boards.greenhouse.io"
import requests

# Add user-agent header for Google
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

# Use a public SearXNG instance (no local setup needed)
SEARXNG_URL = "http://localhost:8080"
# SEARXNG_URL = "https://searx.be"  # or try: https://search.auraes.de

SITES = [
    "boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "site:myworkdayjobs.com"
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
                # Build query without site: prefix (filter manually instead)
                query = f'"{role}" "{include}" site:{site}'
                search_query(query)

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

# iterate_queries()
search_query('"software engineer" "remote" site:boards.greenhouse.io')