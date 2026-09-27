"""Configuration and shared constants for job search application."""

import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
PASSWORD = os.getenv('POSTGRES_PASSWORD')
if not PASSWORD:
    raise ValueError("POSTGRES_PASSWORD environment variable not set")
DATABASE_URL = f"postgresql://postgres:{PASSWORD}@localhost:5432/apply_jobs"

# Timing
TIMER = 3
RATE_LIMITED_SECONDS = 30

# SearXNG configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

SEARXNG_URL = "http://localhost:8080"
ENGINES = "bing,duckduckgo,brave,google"

# Job search parameters
SITES = [
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "myworkdayjobs.com",
    "myworkdaysite.com", 
    "apply.workable.com",
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
    "icims.com",
    "oraclecloud.com",
    "taleo.net",
    "eightfold.ai",
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

# Job filtering
EXCLUDE = ["senior", "staff", "principal", "lead", "intern", "sr", "snr"]
