import win32evtlog
from datetime import datetime, timedelta
from typing import Optional


def filter_events(
    events: list[dict],
    levels: Optional[list[int]] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    source: Optional[str] = None,
    event_id: Optional[int] = None,
) -> list[dict]:
    """Filter a list of events by level, date range, source and event ID.

    Args:
        events: Raw events from log_reader.
        levels: List of win32evtlog EventType values to include.
        date_from: Lower bound for TimeGenerated.
        date_to: Upper bound for TimeGenerated.
        source: Case-insensitive substring match on SourceName.
        event_id: Exact match on EventID.

    Returns:
        Filtered list of event dicts.
    """
    if levels is None:
        levels = [win32evtlog.EVENTLOG_ERROR_TYPE, win32evtlog.EVENTLOG_WARNING_TYPE]

    result = []
    for ev in events:
        if ev["EventType"] not in levels:
            continue
        if date_from and ev["TimeGenerated"] < date_from:
            continue
        if date_to and ev["TimeGenerated"] > date_to:
            continue
        if source and source.lower() not in ev["SourceName"].lower():
            continue
        if event_id is not None and ev["EventID"] != event_id:
            continue
        result.append(ev)

    return result
