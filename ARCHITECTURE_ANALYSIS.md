# Job Search Application - Architecture Analysis

## Current Modular Structure

### Overview

Your project is well-structured with clear separation of concerns across modules:

```
src/
├── main.py           # Configuration, orchestration, counters
├── search.py         # Search execution (SearXNG queries)
├── parse_jobs.py     # Result filtering & company name extraction
├── db_write.py       # Database persistence
└── start_docker.py   # Docker management (placeholder)
```

### Module Responsibilities

**main.py**

- Global configuration (TIMER, ENGINES, SITES, ROLES, LOCATIONS, EXCLUDE)
- Database setup
- Counter tracking (TOTAL_JOBS_FOUND, TOTAL_VALID_JOBS, TOTAL_JOBS_EXCLUDED)
- Orchestration entry point (iterate_queries, search_query calls)

**search.py**

- `Search.search_query()`: Executes SearXNG API calls with pagination & error handling
- Rate limiting & exponential backoff logic
- Returns raw search results

**parse_jobs.py**

- `extract_company_name()`: Multi-strategy company name extraction from URLs
- `parse_query_results()`: Filters results by keywords and site matching
- Creates Job objects from filtered results

**db_write.py**

- `write_results_to_database()`: Persists Job objects to PostgreSQL
- `write_excluded_to_database()`: Logs excluded jobs with reasons
- Duplicate detection by URL

---

## Data Flow

```
search.py (Query SearXNG)
    ↓ raw results {title, url, content}
parse_jobs.py (Extract & Filter)
    ↓ {url, title, company, location}
db_write.py (Save to DB)
    ↓ Job + ExcludedJob records
```

---

## Proposed Architecture for AI Agent HTML Fetching

### Phase 1: HTML Retrieval Layer (Next Step)

Add a new module `src/html_fetcher.py`:

```python
class HTMLFetcher:
    """Fetch and cache HTML content from job posting URLs"""

    def fetch_job_html(self, url: str) -> Optional[str]:
        """Fetch HTML, with retry logic and caching"""
        # 1. Check if already cached in DB
        # 2. Attempt fetch with timeout
        # 3. Store in database
        # 4. Handle errors gracefully

    def batch_fetch(self, urls: List[str]) -> Dict[str, str]:
        """Fetch multiple URLs with rate limiting"""
        # Distribute fetches over time to avoid rate limits
```

**New Database Field:**

- `Job.html_content` (TEXT, nullable)
- `Job.html_fetched_at` (TIMESTAMP, nullable)
- `Job.fetch_error` (VARCHAR, nullable)

---

### Phase 2: AI Agent Integration

Create `src/ai_agent.py`:

```python
class JobAnalysisAgent:
    """Local AI agent for job posting analysis"""

    def extract_job_details(self, html: str) -> Dict:
        """Use local LLM to extract:
        - Required qualifications
        - Nice-to-have skills
        - Tech stack
        - Salary range
        - Benefits
        - Experience level
        """

    def match_job_profile(self, job_details: Dict, user_profile: Dict) -> float:
        """Score job match percentage (0-100)"""

    def generate_application_note(self, job_details: Dict) -> str:
        """Generate personalized application talking points"""
```

**New Database Fields:**

- `Job.extracted_details` (JSONB)
- `Job.match_score` (FLOAT)
- `Job.ai_analyzed_at` (TIMESTAMP)

---

### Phase 3: Revised Pipeline

```
1. search.py
   └─ Get candidate URLs

2. parse_jobs.py
   └─ Filter results

3. db_write.py
   └─ Save Job records (status: "found")

4. html_fetcher.py [NEW]
   └─ Fetch HTML for each Job
   └─ Update Job.html_content

5. ai_agent.py [NEW]
   └─ Analyze HTML with local LLM
   └─ Extract job details
   └─ Calculate match score

6. Update Job record with analysis results
```

---

## Implementation Recommendations

### Immediate Improvements (Before AI Integration)

1. **Fix Search.py class structure**
   - Missing `self` parameter in methods
   - Should pass `HEADERS`, `SEARXNG_URL`, `ENGINES` to constructor
2. **Extract configuration to separate file**

   ```python
   # config.py
   SITES = [...]
   ROLES = [...]
   LOCATIONS = [...]
   EXCLUDE = [...]
   ```

3. **Add logging instead of print statements**

   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```

4. **Create enums for job statuses**
   ```python
   class JobStatus(Enum):
       FOUND = "found"
       HTML_FETCHED = "html_fetched"
       AI_ANALYZED = "ai_analyzed"
       READY_TO_APPLY = "ready_to_apply"
   ```

---

### Database Schema Updates

```sql
-- Existing
ALTER TABLE jobs ADD COLUMN status VARCHAR DEFAULT 'found';
ALTER TABLE jobs ADD COLUMN html_content TEXT;
ALTER TABLE jobs ADD COLUMN html_fetched_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN fetch_error VARCHAR;

-- For AI agent phase
ALTER TABLE jobs ADD COLUMN extracted_details JSONB;
ALTER TABLE jobs ADD COLUMN match_score FLOAT;
ALTER TABLE jobs ADD COLUMN ai_analyzed_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN application_notes TEXT;

-- Tracking
CREATE TABLE job_processing_log (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    stage VARCHAR(50),
    status VARCHAR(20),
    error_message TEXT,
    processed_at TIMESTAMP DEFAULT NOW()
);
```

---

### Local AI Options

**Lightweight Options (Local, No GPU needed):**

- **Ollama** with Mistral 7B or Llama 2 7B
- **LM Studio** UI + API for local models
- **Hugging Face `transformers`** (requires more setup)

**Integration:**

```python
# Using Ollama (simplest)
import requests

response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'mistral',
        'prompt': f"Extract job requirements from: {html}",
        'stream': False
    }
)
```

---

### Error Handling Strategy

For AI agent phase, create `src/error_handler.py`:

```python
class FetchError(Exception):
    """HTML fetch failure"""

class AnalysisError(Exception):
    """AI analysis failure"""

class RateLimitError(Exception):
    """Rate limited by target site"""
```

Each module should:

1. Log the error
2. Store in database for retry
3. Continue processing other jobs
4. Report summary at end

---

## Suggested Execution Order

1. ✅ **Current**: Search → Parse → Store URLs
2. **Next**: Add HTML fetching layer (html_fetcher.py)
3. **Then**: Add local AI agent (ai_agent.py)
4. **Finally**: Create web UI for browsing analyzed jobs with match scores

---

## Questions for AI Agent Design

Before implementing Phase 2-3, clarify:

1. **User Profile**: What data should the agent know about you?
   - Years of experience?
   - Tech stack preferences?
   - Salary expectations?
   - Remote-only requirement?

2. **Analysis Focus**: What should the AI extract/score?
   - Required skills match?
   - Company reputation/funding?
   - Compensation estimation?
   - Growth potential?

3. **Local LLM Choice**: Do you have preferences?
   - Speed vs accuracy trade-off?
   - GPU available or CPU-only?
   - Privacy requirements?

---

## File Organization Suggestion

```
src/
├── __init__.py
├── main.py              # Orchestration
├── config.py            # [NEW] Configuration constants
├── models/              # [NEW] Data models & enums
│   └── job.py
├── search.py            # Search execution (fix class)
├── parse_jobs.py        # Filtering & parsing
├── db_write.py          # Database operations
├── html_fetcher.py      # [NEW] HTML retrieval layer
├── ai_agent.py          # [NEW] Local LLM integration
├── error_handler.py     # [NEW] Exception classes & logging
└── utils/               # [NEW] Helper functions
    └── url_utils.py

models/                 # SQLAlchemy models
├── base.py
├── Job.py
└── ExcludedJob.py

tests/                  # Unit tests
├── test_parse_jobs.py
├── test_html_fetcher.py
└── test_ai_agent.py
```

---

## Metrics to Track

Add to your counter system:

```python
TOTAL_HTML_FETCHED = 0
TOTAL_HTML_FETCH_ERRORS = 0
TOTAL_AI_ANALYZED = 0
TOTAL_AI_ANALYSIS_ERRORS = 0
AVERAGE_MATCH_SCORE = 0.0
```

This will help monitor pipeline health at each stage.
