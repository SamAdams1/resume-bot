from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from pathlib import Path
import json

from backend.src.config import DATABASE_URL
from backend.src.search import search_query

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from backend.models.Job import Job
from backend.models.ExcludedJob import ExcludedJob


class SearchRequest(BaseModel):
    locations: list[str]
    titles: list[str]
    sites: list[str]
    excludes: list[str] = []


class SearchConfig(BaseModel):
    locations: str = ""
    positionTitles: str = ""
    jobBoardSites: str = ""
    excludeKeywords: str = ""
    timestamp: int


app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root(name:str):
    return {"message": f"Welcome to the job search API, {name.capitalize()}"}

@app.get("/jobs")
def read_jobs_db():
    session = SessionLocal()
    try:
        jobs = session.query(Job).all()
        return jobs
    except Exception as e:
        return {"message": "Error occurred while fetching jobs from the database", "error": str(e)}
    finally:
        session.close()

@app.get("/jobs/location/{location}")
def read_job_by_location(location: str):
    session = SessionLocal()
    try:
        jobs = session.query(Job).filter(Job.location.ilike(location)).all()
        if jobs:
            return jobs
        return {"message": f"Jobs with location={location} not found."}
    except Exception as e:
        return {"message": f"Error occurred while fetching jobs from the database filtered by location={location}", "error": str(e)}
    finally:
        session.close()


@app.get("/excludedJobs")
def read_excluded_jobs_db():
    session = SessionLocal()
    try:
        excluded_jobs = session.query(ExcludedJob).all()
        return excluded_jobs
    except Exception as e:
        return {"message": "Error occurred while fetching excluded jobs from the database", "error": str(e)}
    finally:
        session.close()

@app.get("/excludedJobs/location/{location}")
def read_excluded_job_by_location(location: str):
    session = SessionLocal()
    try:
        jobs = session.query(ExcludedJob).filter(ExcludedJob.location.ilike(location)).all()
        if jobs:
            return jobs
        return {"message": f"Excluded jobs with location={location} not found."}
    except Exception as e:
        return {"message": f"Error occurred while fetching excluded jobs from the database filtered by location={location}", "error": str(e)}
    finally:
        session.close()


@app.post("/search")
def start_search(request: SearchRequest):
    """Start a job search with the provided parameters.
    
    Args:
        request: SearchRequest containing locations, titles, and sites
        
    Returns:
        dict with total_results count
    """
    try:
        if not request.locations or not request.titles or not request.sites:
            raise HTTPException(status_code=400, detail="All fields are required")
        
        total_results = 0
        
        # Run search for each combination of location, title, and site
        for location in request.locations:
            for title in request.titles:
                for site in request.sites:
                    print(f"\nSearching for: {title} in {location} on {site}")
                    results = search_query(title, location, site)
                    total_results += results
        
        return {
            "status": "completed",
            "total_results": total_results,
            "message": f"Search completed with {total_results} total results found"
        }
        
    except Exception as e:
        print(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search-config/save")
def save_search_config(config: SearchConfig):
    """Save search configuration to a JSON file."""
    try:
        config_dir = Path(__file__).parent.parent.parent / "search_config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / "search_config.json"
        
        config_data = config.dict()
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return {"status": "success", "message": "Search config saved"}
    except Exception as e:
        print(f"Error saving search config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")


@app.get("/search-config/load")
def load_search_config():
    """Load search configuration from JSON file."""
    try:
        config_dir = Path(__file__).parent.parent.parent / "search_config"
        config_file = config_dir / "search_config.json"
        
        if not config_file.exists():
            return None
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return SearchConfig(**config_data)
    except Exception as e:
        print(f"Error loading search config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load config: {str(e)}")


@app.post("/search-config/clear")
def clear_search_config():
    """Clear search configuration file."""
    try:
        config_dir = Path(__file__).parent.parent.parent / "search_config"
        config_file = config_dir / "search_config.json"
        
        if config_file.exists():
            config_file.unlink()
        
        return {"status": "success", "message": "Search config cleared"}
    except Exception as e:
        print(f"Error clearing search config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear config: {str(e)}")
