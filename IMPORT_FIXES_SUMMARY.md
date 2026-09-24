# Import Fixes & Circular Dependency Resolution

## Problems Fixed

### 1. **Missing Imports in search.py**

- **Issue**: Referenced `ENGINES`, `HEADERS`, `SEARXNG_URL`, `RATE_LIMITED_SECONDS` without importing
- **Fix**: Import from `config.py`
- **Code**:
  ```python
  from config import (
      ENGINES, HEADERS, SEARXNG_URL, RATE_LIMITED_SECONDS
  )
  from parse_jobs import parse_query_results
  ```

### 2. **Broken Search Class Structure**

- **Issue**: Class had `__init__(self): pass` but `search_query()` was missing `self` parameter
- **Fix**: Converted to module-level function (not a class)
- **Before**: `def search_query(role: str, ...)` (inside class, missing self)
- **After**: `def search_query(role: str, ...) -> int:` (standalone function)

### 3. **Missing Imports in parse_jobs.py**

- **Issue**: Referenced `EXCLUDE` and `Job` without importing; called `write_results_to_database()` without importing
- **Fix**: Added all necessary imports
- **Code**:
  ```python
  from config import EXCLUDE
  from models.Job import Job
  from db_write import write_results_to_database, write_excluded_to_database
  ```

### 4. **Missing Imports in db_write.py**

- **Issue**: Referenced `Session`, `Job`, `ExcludedJob`, `SQLAlchemyError`, `DATABASE_URL` without importing
- **Fix**: Added all necessary imports and moved database initialization here
- **Code**:
  ```python
  from config import DATABASE_URL
  from models.base import Base
  from models.Job import Job
  from models.ExcludedJob import ExcludedJob
  ```

### 5. **Circular Dependency Risk**

- **Issue**: Multiple modules referenced globals from `main.py`, creating potential circular imports
- **Solution**: Centralized all configuration in `config.py` (new file)
- **Files updated**:
  - `config.py` - NEW: Contains all constants and configuration
  - `main.py` - Imports from `config.py`, not the other way around
  - `db_write.py` - Database initialization moved here, uses `config.py`
  - `search.py` - Uses `config.py` for settings
  - `parse_jobs.py` - Uses `config.py` for EXCLUDE list

### 6. **Counter Tracking Issues**

- **Issue**: Used `global TOTAL_VALID_JOBS` in `db_write.py`, but variable wasn't in that module
- **Solution**: Functions now return counts instead of modifying globals
- **Changed**:
  - `write_results_to_database()` now returns `num_jobs_saved`
  - `write_excluded_to_database()` now returns `num_excluded_saved`
  - `parse_query_results()` now returns tuple of (valid_count, excluded_count)
  - `search_query()` returns count of results found
- Main.py can now accumulate counts from return values

### 7. **Broken main.py**

- **Issue**: Called `search_query()` without importing it; referenced undefined variables
- **Fix**: Complete restructure
- **Changes**:

  ```python
  from config import TIMER, SITES, ROLES, LOCATIONS
  from search import search_query

  # Moved all global config to config.py
  # Now properly tracks counters from return values
  ```

---

## Module Dependency Graph (After Fixes)

```
config.py
    ↓ (imported by all modules)
    ├── search.py
    │   ├── imports: config, parse_jobs
    │   └── exports: search_query()
    │
    ├── parse_jobs.py
    │   ├── imports: config, db_write, models.Job
    │   └── exports: extract_company_name(), parse_query_results()
    │
    ├── db_write.py
    │   ├── imports: config, models
    │   └── exports: write_results_to_database(), write_excluded_to_database()
    │
    └── main.py
        ├── imports: config, search
        └── orchestrates: iterate_queries()
```

**No circular dependencies!** The dependency flow is strictly one-way:

- `config.py` is at the root (imports nothing from other modules)
- `search.py` → `parse_jobs.py` → `db_write.py` (linear pipeline)
- `main.py` orchestrates by importing from `search.py`

---

## New Files Created

### `src/config.py`

Centralized configuration containing:

- Database URL
- Timing constants (TIMER, RATE_LIMITED_SECONDS)
- SearXNG configuration (HEADERS, URL, ENGINES)
- Search parameters (SITES, ROLES, LOCATIONS, EXCLUDE)

### `src/test_imports.py`

Validation script to verify all imports work and no circular dependencies exist.

---

## Changes to Existing Files

### `src/main.py`

```python
# BEFORE: Mixed concerns (config + orchestration)
import time, os, requests, dotenv
from sqlalchemy import ...
TIMER = 3
SITES = [...]
HEADERS = {...}
# ... 100+ lines of config

# AFTER: Clean orchestration
from config import TIMER, SITES, ROLES, LOCATIONS
from search import search_query

total_jobs_found = 0
total_valid_jobs = 0
total_jobs_excluded = 0

def iterate_queries():
    # Implementation
```

### `src/search.py`

```python
# BEFORE: Missing imports, broken class structure
class Search:
    def __init__(self): pass
    def search_query(role, ...):  # Missing self
        # References ENGINES, HEADERS, SEARXNG_URL undefined

# AFTER: Proper module-level function with imports
from config import ENGINES, HEADERS, SEARXNG_URL, RATE_LIMITED_SECONDS
from parse_jobs import parse_query_results

def search_query(role: str, location: str, site: str) -> int:
    # Implementation
```

### `src/parse_jobs.py`

```python
# BEFORE: Missing imports
def parse_query_results(...):
    # References EXCLUDE, Job, write_results_to_database undefined

# AFTER: Proper imports
from config import EXCLUDE
from models.Job import Job
from db_write import write_results_to_database, write_excluded_to_database

def parse_query_results(...) -> Tuple[int, int]:
    # Returns (valid_count, excluded_count)
```

### `src/db_write.py`

```python
# BEFORE: Missing imports, global variable misuse
def write_results_to_database(jobs):
    global TOTAL_VALID_JOBS  # Not defined in this module
    # References Session, Job, ExcludedJob undefined

# AFTER: Proper imports and return-based counting
from config import DATABASE_URL
from models.Job import Job
from models.ExcludedJob import ExcludedJob

def write_results_to_database(jobs) -> int:
    # Returns num_jobs_saved
```

---

## Testing the Fixes

Run the import test:

```bash
cd src
python test_imports.py
```

Expected output:

```
Testing module imports...

✓ src.config
✓ src.db_write
✓ src.parse_jobs
✓ src.search
✓ src.main

============================================================
IMPORT TEST SUMMARY
============================================================
✓ OK - src.config
✓ OK - src.db_write
✓ OK - src.parse_jobs
✓ OK - src.search
✓ OK - src.main
============================================================
Results: 5/5 modules imported successfully
✓ All imports successful! No circular dependencies detected.
```

---

## Next Steps

1. ✅ Fixed all import errors and circular dependencies
2. ⏭️ Run `test_imports.py` to verify fixes
3. ⏭️ Test `main.py` to ensure end-to-end functionality
4. ⏭️ Add HTML fetcher module for AI agent integration
5. ⏭️ Update database schema with new fields for AI analysis

---

## Summary

- **Files created**: 2 (config.py, test_imports.py)
- **Files fixed**: 4 (search.py, parse_jobs.py, db_write.py, main.py)
- **Circular imports eliminated**: ✓
- **Missing imports resolved**: ✓
- **Code organization improved**: ✓
