from core.history import get_connection


def _event_key(ev: dict) -> tuple:
    return (ev.get("SourceName", ""), ev.get("EventID", 0))


def get_latest_analysis_snapshot() -> list[dict]:
    """Fetch the most recent 1000 analysis records from the database.

    Returns a list of dicts with keys: source, event_id, level, message, analyzed_at.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT source, event_id, level, message, analyzed_at "
        "FROM analyses ORDER BY id DESC LIMIT 1000"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def compare_events(current_events: list[dict], previous_analyses: list[dict]) -> dict:
    """Compare current events against previously analyzed ones.

    Returns a dict with three lists:
        - "new": events not seen before
        - "resolved": previously seen events no longer present
        - "repeated": events that appeared before and are still present

    Comparison key is (source, event_id).
    """
    current_keys = {_event_key(ev) for ev in current_events}
    previous_keys = {(r["source"], r["event_id"]) for r in previous_analyses}

    new_events = [ev for ev in current_events if _event_key(ev) not in previous_keys]
    resolved = [r for r in previous_analyses if (r["source"], r["event_id"]) not in current_keys]
    repeated = [ev for ev in current_events if _event_key(ev) in previous_keys]

    return {
        "new": new_events,
        "resolved": resolved,
        "repeated": repeated,
    }
