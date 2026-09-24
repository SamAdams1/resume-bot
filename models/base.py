"""
Shared SQLAlchemy Base for all models.

This module exists to break a circular import dependency:
- main.py needs to import Job and ExcludedJob (the model classes)
- Job.py and ExcludedJob.py need to import Base (to define their tables)
- If Base was defined in main.py, then main.py would import models, which would
  import main.py, creating a circular dependency

By defining Base in its own module, both main.py and the model files can import
it without creating a circular dependency.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
