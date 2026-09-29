# resume-bot

Querying the web:
searxng
Camoufox - anti bot blocking

## todo

- fetch all queries without getting ip blocked
- Increase delays into the minutes.
- Auto detect rate limiting by checking the searxng logs.
- Rotate proxies if rate limited.
- Add camoufox for future agent use.

### Setup:

#### Quick Start (Recommended)

Start everything with a single command from the project root:

```bash
npm start
# or
node cli.js start
```

This automatically starts:

- 🗄️ Docker services (Searxng + Valkey database)
- 🐍 Python backend (FastAPI) at http://localhost:8000
- 🎨 Angular frontend at http://localhost:4200

To stop all services, press `Ctrl+C` or run:

```bash
npm stop
# or
node cli.js stop
```

#### Manual Setup (if needed)

**Start Docker services:**

```bash
docker compose up -d
```

**Start backend in a separate terminal:**

```bash
# Windows
venv\Scripts\activate

# Unix/Mac
source venv/Scripts/activate

uvicorn backend.src.server:app --reload
```

**Start frontend in another terminal:**

```bash
cd frontend
npm start
```

**Stop Docker services:**

```bash
docker compose down
```

#### useful docs:

searxng search settings.yml https://docs.searxng.org/admin/settings/settings_search.html
searxng docker setup https://docs.searxng.org/admin/installation-docker.html

## local web page

This project now includes a one-page local web UI with two views:

- Search View: edit SITES, ENGINES, ROLES, LOCATIONS, EXCLUDE for saved users and run the search loop
- Database View: view rows from jobs and excluded_jobs

### first run

1. Start postgres and searxng as you normally do.
2. Install dependencies:

   pip install -r requirements.txt

3. Start the web app:

   python src/web_app.py

4. Open:

   http://127.0.0.1:5000

### notes

- User profiles are saved to profiles.json in the project root.
- Search output is printed in the terminal and also appended to search_output.txt.
- The UI includes 3 default saved users that you can rename and edit.
