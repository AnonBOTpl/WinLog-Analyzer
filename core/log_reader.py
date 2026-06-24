import atexit
import concurrent.futures
import time
import xml.etree.ElementTree as ET
import win32evtlog
import pywintypes
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

NS = {
    "e": "http://schemas.microsoft.com/win/2004/08/events/event",
}

CLASSIC_LOGS = ["Application", "Security", "Setup", "System"]

EVENT_TYPE_MAP = {
    win32evtlog.EVENTLOG_ERROR_TYPE: "Error",
    win32evtlog.EVENTLOG_WARNING_TYPE: "Warning",
    win32evtlog.EVENTLOG_INFORMATION_TYPE: "Information",
    win32evtlog.EVENTLOG_AUDIT_SUCCESS: "Audit Success",
    win32evtlog.EVENTLOG_AUDIT_FAILURE: "Audit Failure",
}

# Windows Event Log (Evt) XML uses different Level values:
#   1=Critical, 2=Error, 3=Warning, 4=Information, 5=Verbose
EVT_LEVEL_MAP = {
    1: "Critical",
    2: "Error",
    3: "Warning",
    4: "Information",
    5: "Verbose",
}


def _convert_time(pytime: pywintypes.Time) -> datetime:
    return datetime.fromtimestamp(pytime.timestamp(), tz=WARSAW_TZ)


def _parse_iso_time(s: str) -> Optional[datetime]:
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return dt.astimezone(WARSAW_TZ)
    except Exception:
        return None


def _evt_render_xml(handle) -> str:
    return win32evtlog.EvtRender(handle, win32evtlog.EvtRenderEventXml)


_RENDER_TIMEOUT_SECONDS = 10
_RENDER_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1)
atexit.register(_RENDER_EXECUTOR.shutdown)


def _evt_render_xml_with_timeout(handle) -> str | None:
    try:
        future = _RENDER_EXECUTOR.submit(_evt_render_xml, handle)
        return future.result(timeout=_RENDER_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        return None
    except Exception:
        return None


def _parse_event_xml(xml: str, channel: str) -> Optional[dict]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None

    sys_node = root.find("e:System", NS)
    if sys_node is None:
        return None

    def text(tag: str) -> str:
        el = sys_node.find(f"e:{tag}", NS)
        return el.text or "" if el is not None else ""

    def text_int(tag: str) -> int:
        v = text(tag)
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    provider = sys_node.find("e:Provider", NS)
    source = provider.get("Name", "Unknown") if provider is not None else "Unknown"
    event_id = text_int("EventID")
    level = text_int("Level")

    tc = sys_node.find("e:TimeCreated", NS)
    time_str = tc.get("SystemTime", "") if tc is not None else ""
    ts = _parse_iso_time(time_str) if time_str else None
    if ts is None:
        return None

    level_name = EVT_LEVEL_MAP.get(level, f"Unknown ({level})")

    ch_el = sys_node.find("e:Channel", NS)
    channel_from_xml = ch_el.text if ch_el is not None else channel

    data_node = root.find("e:EventData", NS)
    msg = ""
    if data_node is not None:
        parts = []
        for data in data_node.findall("e:Data", NS):
            txt = data.text or ""
            name = data.get("Name", "")
            if name:
                parts.append(f"{name}: {txt}")
            else:
                parts.append(txt)
        msg = "\n".join(parts)

    if not msg:
        msg_node = root.find("e:UserData", NS)
        if msg_node is not None:
            msg = ET.tostring(msg_node, encoding="unicode", method="text").strip()

    return {
        "TimeGenerated": ts,
        "SourceName": source,
        "EventID": event_id,
        "EventType": level,
        "Level": level_name,
        "Message": msg,
        "Data": [],
        "LogType": channel_from_xml,
        "LogSource": channel_from_xml,
    }


def get_all_sources() -> list[str]:
    """Enumerate all available Windows Event Log channels.

    Starts with classic logs (Application, Security, Setup, System)
    and then scans all registered channels via EvtOpenChannelEnum.
    Returns a sorted list of channel names.
    """
    available = set()

    for name in CLASSIC_LOGS:
        try:
            handle = win32evtlog.OpenEventLog(None, name)
            win32evtlog.CloseEventLog(handle)
            available.add(name)
        except pywintypes.error:
            pass

    try:
        enum = win32evtlog.EvtOpenChannelEnum(None)
        while True:
            path = win32evtlog.EvtNextChannelPath(enum)
            if not path:
                break
            available.add(path)
    except Exception:
        pass

    return sorted(available)


_QUERYABLE_CACHE: dict[str, tuple[bool, float]] = {}
_CACHE_TTL_SECONDS = 300.0

EXCLUDED_CHANNEL_PATTERNS = (
    "Analytic", "Debug", "Diagnostic", "Performance", "Trace",
    "Diagnosis", "Diag", "WDI", "Perf",
)


def _is_queryable(channel: str) -> bool:
    now = time.time()

    if channel in _QUERYABLE_CACHE:
        cached_val, cached_at = _QUERYABLE_CACHE[channel]
        if now - cached_at < _CACHE_TTL_SECONDS:
            return cached_val

    for pat in EXCLUDED_CHANNEL_PATTERNS:
        if pat.lower() in channel.lower():
            _QUERYABLE_CACHE[channel] = (False, now)
            return False

    try:
        qh = win32evtlog.EvtQuery(
            channel,
            win32evtlog.EvtQueryChannelPath,
            "*",
            None,
        )
        qh.Close()
        _QUERYABLE_CACHE[channel] = (True, now)
        return True
    except Exception:
        _QUERYABLE_CACHE[channel] = (False, now)
        return False


def _query_channel(
    channel: str,
    max_events: int,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    only_errors: bool = True,
) -> list[dict]:
    """Query a single channel using EvtQuery."""
    if not _is_queryable(channel):
        return []

    query = "*[System[(Level=2 or Level=3)]]" if only_errors else "*"

    result = []
    try:
        qhandle = win32evtlog.EvtQuery(
            channel,
            win32evtlog.EvtQueryChannelPath | win32evtlog.EvtQueryReverseDirection,
            query,
            None,
        )
    except pywintypes.error:
        return result

    try:
        while len(result) < max_events:
            batch = win32evtlog.EvtNext(qhandle, 100, 1000, 0)
            if not batch:
                break

            for evt_handle in batch:
                if len(result) >= max_events:
                    evt_handle.Close()
                    continue

                try:
                    xml = _evt_render_xml_with_timeout(evt_handle)
                    if xml is None:
                        evt_handle.Close()
                        continue
                    event = _parse_event_xml(xml, channel)
                    if event:
                        if date_from and event["TimeGenerated"] < date_from:
                            continue
                        if date_to and event["TimeGenerated"] > date_to:
                            continue
                        result.append(event)
                except Exception:
                    pass
                finally:
                    evt_handle.Close()
    except pywintypes.error:
        pass
    finally:
        try:
            qhandle.Close()
        except Exception:
            pass

    return result


def get_events_from_sources(
    sources: list[str],
    max_events: int = 2000,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    only_errors: bool = True,
) -> list[dict]:
    """Fetch events from multiple channels with sequential priority.

    Classic logs (Application, Security, etc.) are queried first,
    then other sources. Results are sorted by time descending.

    Args:
        sources: List of channel names from get_all_sources().
        max_events: Maximum total events to return.
        date_from: Lower bound for TimeGenerated.
        date_to: Upper bound for TimeGenerated.
        only_errors: If True, only fetch Level=2 (Error) and Level=3 (Warning).

    Returns:
        List of event dicts sorted by TimeGenerated descending.
    """
    all_events = []

    priority = [s for s in CLASSIC_LOGS if s in sources]
    rest = [s for s in sources if s not in priority]
    ordered = priority + rest

    for src in ordered:
        if len(all_events) >= max_events:
            break

        remaining = max_events - len(all_events)
        evts = _query_channel(src, remaining, date_from, date_to, only_errors)
        if evts:
            all_events.extend(evts)

    all_events.sort(key=lambda e: e["TimeGenerated"], reverse=True)
    return all_events[:max_events]


