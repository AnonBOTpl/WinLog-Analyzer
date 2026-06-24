from PyQt6.QtCore import QThread, pyqtSignal
from core.ai_client import analyze_event
from core.log_reader import get_all_sources, get_events_from_sources


class LoadEventsWorker(QThread):
    """Background worker that loads Windows Event Log events.

    Signals:
        finished(list, list): Emitted with (sources, events) on success.
        error(str): Emitted with the error message on failure.
    """
    finished = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, max_events: int = 10000):
        super().__init__()
        self.max_events = max_events

    def run(self):
        try:
            sources = get_all_sources()
            events = get_events_from_sources(sources, max_events=self.max_events, only_errors=True)
            self.finished.emit(sources, events)
        except Exception as e:
            self.error.emit(str(e))


class AnalysisWorker(QThread):
    """Background worker that sends a single event to an AI provider.

    Signals:
        finished(dict): Emitted with the parsed AI analysis result.
        error(str): Emitted with the error message on failure.
    """
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, provider_name: str, api_key: str, model: str, event: dict):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.event = event

    def run(self):
        result = analyze_event(self.provider_name, self.api_key, self.model, self.event)
        if "error" in result:
            self.error.emit(result["error"])
        else:
            self.finished.emit(result)


class BatchAnalysisWorker(QThread):
    """Background worker that analyzes multiple events sequentially.

    Processes events one by one with a 1-second pause between requests.
    A single event failure does not abort the entire batch.

    Signals:
        progress(int, int): Emitted with (current, total) count.
        event_done(int, dict): Emitted with (index, result) on each success.
        event_error(int, str): Emitted with (index, error) on each failure.
        finished(): Emitted when all events have been processed (or cancelled).
    """
    progress = pyqtSignal(int, int)
    event_done = pyqtSignal(int, dict)
    event_error = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, provider_name: str, api_key: str, model: str, events: list[dict]):
        super().__init__()
        self.provider_name = provider_name
        self.api_key = api_key
        self.model = model
        self.events = events
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the batch analysis."""
        self._cancelled = True

    def run(self):
        total = len(self.events)
        for i, ev in enumerate(self.events):
            if self._cancelled:
                break
            result = analyze_event(self.provider_name, self.api_key, self.model, ev)
            if self._cancelled:
                break
            if "error" in result:
                self.event_error.emit(i, result["error"])
            else:
                self.event_done.emit(i, result)
            self.progress.emit(i + 1, total)
            if i < total - 1 and not self._cancelled:
                QThread.msleep(1000)
        self.finished.emit()
