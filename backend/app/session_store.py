import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SESSIONS_FILE = DATA_DIR / "sessions.json"

_LOCK = Lock()
_SESSIONS: dict[str, dict] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_sessions() -> None:
    global _SESSIONS
    with _LOCK:
        if not SESSIONS_FILE.exists():
            _SESSIONS = {}
            return
        try:
            _SESSIONS = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _SESSIONS = {}


def save_sessions() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps(_SESSIONS, ensure_ascii=False, indent=2), encoding="utf-8")


def create_session(os: str = "Unknown") -> dict:
    session_id = str(uuid.uuid4())
    now = _now()
    session = {
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "messages": [],
        "active_issue": None,
        "last_analysis": None,
        "tried_steps": [],
        "issue_category": None,
        "os": os,
    }
    with _LOCK:
        _SESSIONS[session_id] = session
        save_sessions()
    return session


def get_or_create_session(session_id: str | None, os: str = "Unknown") -> dict:
    with _LOCK:
        if session_id and session_id in _SESSIONS:
            session = _SESSIONS[session_id]
            session["os"] = os or session.get("os") or "Unknown"
            session["updated_at"] = _now()
            save_sessions()
            return session
    return create_session(os)


def list_sessions() -> list[dict]:
    with _LOCK:
        return [
            {
                "session_id": session["session_id"],
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
                "title": _session_title(session),
                "issue_category": session.get("issue_category"),
                "os": session.get("os"),
            }
            for session in sorted(_SESSIONS.values(), key=lambda item: item.get("updated_at", ""), reverse=True)
        ]


def get_session(session_id: str) -> dict | None:
    with _LOCK:
        return _SESSIONS.get(session_id)


def delete_session(session_id: str) -> bool:
    with _LOCK:
        deleted = _SESSIONS.pop(session_id, None) is not None
        if deleted:
            save_sessions()
        return deleted


def add_message(session: dict, role: str, content: str, analysis: dict | None = None) -> None:
    session["messages"].append({"role": role, "content": content, "timestamp": _now(), "analysis": analysis})
    session["updated_at"] = _now()
    with _LOCK:
        _SESSIONS[session["session_id"]] = session
        save_sessions()


def update_active_issue(session: dict, message: str, os: str, analysis: dict, tried_steps: list[str] | None = None) -> None:
    tried_steps = tried_steps or []
    existing_tried = session.get("tried_steps", [])
    merged_tried = list(dict.fromkeys(existing_tried + tried_steps))
    session["last_analysis"] = analysis
    session["issue_category"] = analysis.get("category")
    session["os"] = os
    session["tried_steps"] = merged_tried
    session["active_issue"] = {
        "topic": _session_title(session) if session.get("active_issue") else message[:120],
        "category": analysis.get("category"),
        "os": os,
        "known_facts": _known_facts_from_messages(session),
        "tried_steps": merged_tried,
        "last_solution_steps": analysis.get("solution_steps", []),
    }
    session["updated_at"] = _now()
    with _LOCK:
        _SESSIONS[session["session_id"]] = session
        save_sessions()


def _session_title(session: dict) -> str:
    for message in session.get("messages", []):
        if message.get("role") == "user" and message.get("content"):
            return message["content"][:60]
    active_issue = session.get("active_issue") or {}
    return active_issue.get("topic") or "Yeni sohbet"


def _known_facts_from_messages(session: dict) -> list[str]:
    facts = []
    for message in session.get("messages", []):
        if message.get("role") == "user" and message.get("content"):
            facts.append(message["content"][:160])
    return facts[-5:]


load_sessions()
