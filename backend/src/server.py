from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from backend.src.config import DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from backend.models.Job import Job
from backend.models.ExcludedJob import ExcludedJob


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

