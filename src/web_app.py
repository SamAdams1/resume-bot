"""Local web UI for running searches and viewing database tables.

Run with:
    python src/web_app.py
"""

from __future__ import annotations

import json
import sys
import threading
import uuid
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

import parse_jobs
import search
from db_write import Session
from models.ExcludedJob import ExcludedJob
from models.Job import Job

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILES_PATH = BASE_DIR / "profiles.json"
SEARCH_OUTPUT_PATH = BASE_DIR / "search_output.txt"

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))


DEFAULT_PROFILES = [
    {
        "id": "user-1",
        "name": "Alex",
        "sites": ["boards.greenhouse.io", "jobs.lever.co"],
        "engines": "bing,duckduckgo",
        "roles": ["software engineer", "backend engineer"],
        "locations": ["remote", "New Hampshire"],
        "exclude": ["senior", "staff", "principal"],
    },
    {
        "id": "user-2",
        "name": "Blake",
        "sites": ["jobs.ashbyhq.com", "myworkdayjobs.com"],
        "engines": "brave,google",
        "roles": ["frontend engineer", "full stack engineer"],
        "locations": ["remote", "Boston"],
        "exclude": ["intern", "lead", "principal"],
    },
    {
        "id": "user-3",
        "name": "Casey",
        "sites": ["apply.workable.com", "jobs.smartrecruiters.com"],
        "engines": "duckduckgo,google",
        "roles": ["web developer", "software developer"],
        "locations": ["remote", "New York"],
        "exclude": ["senior", "sr", "staff"],
    },
]


search_state: dict[str, Any] = {
    "running": False,
    "run_id": None,
    "started_at": None,
    "finished_at": None,
    "progress": {
        "current": 0,
        "total": 0,
        "current_item": "",
    },
    "summary": {
        "queries_completed": 0,
        "results_found": 0,
    },
    "logs": [],
    "error": None,
}
state_lock = threading.Lock()


class TeeLogger:
    """Capture print output to both terminal and file while updating in-memory progress logs."""

    def __init__(self, file_path: Path) -> None:
        self._file_handle = open(file_path, "a", encoding="utf-8")

    def write(self, text: str) -> int:
        if not text:
            return 0

        sys.__stdout__.write(text)
        sys.__stdout__.flush()
        self._file_handle.write(text)
        self._file_handle.flush()

        cleaned = text.strip()
        if cleaned:
            with state_lock:
                search_state["logs"].append(cleaned)
                # Keep only the most recent logs to avoid unbounded memory growth.
                search_state["logs"] = search_state["logs"][-300:]

        return len(text)

    def flush(self) -> None:
        self._file_handle.flush()

    def close(self) -> None:
        self._file_handle.close()


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_profiles_file() -> None:
    if PROFILES_PATH.exists():
        return

    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_PROFILES, f, indent=2)


def _load_profiles() -> list[dict[str, Any]]:
    _ensure_profiles_file()
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_profiles(profiles: list[dict[str, Any]]) -> None:
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)


def _normalize_list(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        return [v.strip() for v in value if str(v).strip()]

    if not value:
        return []

    lines = str(value).replace(",", "\n").split("\n")
    return [line.strip() for line in lines if line.strip()]


def _run_search_loop(profile: dict[str, Any]) -> None:
    combos = [
        (site, role, location)
        for site in profile["sites"]
        for role in profile["roles"]
        for location in profile["locations"]
    ]

    logger = TeeLogger(SEARCH_OUTPUT_PATH)

    with state_lock:
        search_state["running"] = True
        search_state["run_id"] = str(uuid.uuid4())
        search_state["started_at"] = _timestamp()
        search_state["finished_at"] = None
        search_state["progress"] = {
            "current": 0,
            "total": len(combos),
            "current_item": "",
        }
        search_state["summary"] = {
            "queries_completed": 0,
            "results_found": 0,
        }
        search_state["logs"] = [
            f"[{_timestamp()}] Starting search with profile: {profile['name']}"
        ]
        search_state["error"] = None

    try:
        search.ENGINES = profile["engines"]
        parse_jobs.EXCLUDE = profile["exclude"]

        logger.write(f"\n[{_timestamp()}] Search started for profile {profile['name']}\n")
        logger.write(f"Engines: {profile['engines']}\n")
        logger.write(f"Sites: {', '.join(profile['sites'])}\n")
        logger.write(f"Roles: {', '.join(profile['roles'])}\n")
        logger.write(f"Locations: {', '.join(profile['locations'])}\n")
        logger.write(f"Exclude: {', '.join(profile['exclude'])}\n\n")

        for idx, (site, role, location) in enumerate(combos, start=1):
            with state_lock:
                search_state["progress"]["current"] = idx
                search_state["progress"]["current_item"] = (
                    f"site:{site} | role:{role} | location:{location}"
                )
                search_state["summary"]["queries_completed"] = idx - 1

            logger.write(
                f"\n[{_timestamp()}] ({idx}/{len(combos)}) Querying site:{site} role:{role} location:{location}\n"
            )

            with redirect_stdout(logger):
                result_count = search.search_query(role, location, site)

            with state_lock:
                search_state["summary"]["queries_completed"] = idx
                search_state["summary"]["results_found"] += int(result_count)

        logger.write(
            f"\n[{_timestamp()}] Search complete. Total results found: {search_state['summary']['results_found']}\n"
        )

    except Exception as exc:  # Broad catch keeps UI responsive and exposes failures.
        with state_lock:
            search_state["error"] = str(exc)
        logger.write(f"\n[{_timestamp()}] ERROR: {exc}\n")

    finally:
        with state_lock:
            search_state["running"] = False
            search_state["finished_at"] = _timestamp()

        logger.write(f"[{_timestamp()}] Search finished.\n")
        logger.close()


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/profiles")
def get_profiles() -> Any:
    return jsonify(_load_profiles())


@app.post("/api/profiles")
def save_profiles() -> Any:
    payload = request.get_json(silent=True) or {}
    profiles = payload.get("profiles", [])

    cleaned_profiles: list[dict[str, Any]] = []
    for idx, profile in enumerate(profiles):
        cleaned_profiles.append(
            {
                "id": profile.get("id") or f"user-{idx + 1}",
                "name": profile.get("name") or f"User {idx + 1}",
                "sites": _normalize_list(profile.get("sites")),
                "engines": str(profile.get("engines", "")).strip(),
                "roles": _normalize_list(profile.get("roles")),
                "locations": _normalize_list(profile.get("locations")),
                "exclude": _normalize_list(profile.get("exclude")),
            }
        )

    _save_profiles(cleaned_profiles)
    return jsonify({"ok": True, "profiles": cleaned_profiles})


@app.post("/api/search/start")
def start_search() -> Any:
    payload = request.get_json(silent=True) or {}
    profile_id = payload.get("profileId")

    with state_lock:
        if search_state["running"]:
            return jsonify({"ok": False, "error": "Search is already running."}), 409

    profiles = _load_profiles()
    profile = next((p for p in profiles if p.get("id") == profile_id), None)
    if not profile:
        return jsonify({"ok": False, "error": "Profile not found."}), 404

    worker = threading.Thread(target=_run_search_loop, args=(profile,), daemon=True)
    worker.start()

    return jsonify({"ok": True, "message": "Search started."})


@app.get("/api/search/status")
def search_status() -> Any:
    with state_lock:
        return jsonify(search_state)


def _serialize_jobs(limit: int = 200) -> list[dict[str, Any]]:
    session = Session()
    try:
        rows = session.query(Job).order_by(Job.date_found.desc()).limit(limit).all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "company": row.company,
                "location": row.location,
                "url": row.url,
                "date_found": row.date_found.isoformat() if row.date_found else None,
                "applied": row.applied,
            }
            for row in rows
        ]
    finally:
        session.close()


def _serialize_excluded(limit: int = 200) -> list[dict[str, Any]]:
    session = Session()
    try:
        rows = session.query(ExcludedJob).order_by(ExcludedJob.date_found.desc()).limit(limit).all()
        return [
            {
                "id": row.id,
                "query": row.query,
                "title": row.title,
                "url": row.url,
                "reason": row.reason,
                "date_found": row.date_found.isoformat() if row.date_found else None,
            }
            for row in rows
        ]
    finally:
        session.close()


@app.get("/api/db/jobs")
def db_jobs() -> Any:
    return jsonify({"rows": _serialize_jobs()})


@app.get("/api/db/excluded-jobs")
def db_excluded_jobs() -> Any:
    return jsonify({"rows": _serialize_excluded()})


if __name__ == "__main__":
    # Keep debug off so the search background thread is not duplicated by reloader.
    app.run(host="127.0.0.1", port=5000, debug=False)
