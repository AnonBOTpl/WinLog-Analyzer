from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from core.i18n import t


COLOR_ERROR = QColor("#E74C3C")
COLOR_WARNING = QColor("#F39C12")
COLOR_DEFAULT = QColor("#ECF0F1")
COLOR_BG = QColor("#16213E")

LEVEL_COLORS = {
    "Error": COLOR_ERROR,
    "Warning": COLOR_WARNING,
}


def _event_key(ev: dict) -> tuple:
    return (ev.get("SourceName", ""), ev.get("EventID", 0), str(ev.get("TimeGenerated", "")))


class LogTable(QTableWidget):
    event_selected = pyqtSignal(object)
    checked_count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._events = []
        self._all_events = []
        self._active_filter = "all"
        self._search_text = ""
        self._search_column = -1
        self._checked: set[tuple] = set()
        self._setup_ui()
        self.itemChanged.connect(self._on_item_changed)

    def _setup_ui(self):
        headers = ["", t("table_col_datetime"), t("table_col_level"), t("table_col_source"), t("table_col_event_id"), t("table_col_description")]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setColumnWidth(0, 30)
        self.setColumnWidth(1, 160)
        self.setColumnWidth(2, 90)
        self.setColumnWidth(3, 160)
        self.setColumnWidth(4, 80)

        self.itemSelectionChanged.connect(self._on_selection_changed)

    def set_events(self, events: list[dict]):
        self._all_events = events
        self._apply_filter()

    def filter_by_source(self, source: str | None):
        self._active_filter = source or "all"
        self._apply_filter()

    def set_search_filter(self, text: str, column: int = -1):
        self._search_text = text.lower()
        self._search_column = column
        self._apply_filter()

    def _apply_filter(self):
        self._events = []
        for ev in self._all_events:
            if self._active_filter not in (None, "all"):
                if self._active_filter == "critical":
                    if ev.get("EventType") not in (1, 2):
                        continue
                elif ev.get("LogSource") != self._active_filter:
                    continue

            if self._search_text:
                if self._search_column == -1:
                    searchable = [
                        ev.get("SourceName", ""),
                        str(ev.get("EventID", "")),
                        ev.get("Message", ""),
                        ev.get("Level", ""),
                    ]
                    if not any(self._search_text in s.lower() for s in searchable):
                        continue
                else:
                    col_map = {2: "SourceName", 3: "EventID", 4: "Message"}
                    key = col_map.get(self._search_column)
                    if key:
                        val = str(ev.get(key, ""))
                        if self._search_text not in val.lower():
                            continue

            self._events.append(ev)

        self.setSortingEnabled(False)
        self.setUpdatesEnabled(False)
        self.blockSignals(True)
        self.setRowCount(len(self._events))

        for row, ev in enumerate(self._events):
            dt = ev["TimeGenerated"].strftime("%Y-%m-%d %H:%M:%S")
            level = ev["Level"]
            color = LEVEL_COLORS.get(level, COLOR_DEFAULT)

            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            checked = _event_key(ev) in self._checked
            cb_item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.setItem(row, 0, cb_item)

            items = [
                (dt, color),
                (level, color),
                (ev["SourceName"], color),
                (str(ev["EventID"]), color),
                (ev["Message"][:120], color),
            ]

            for col, (text, clr) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setForeground(clr)
                item.setBackground(COLOR_BG)
                self.setItem(row, col + 1, item)

        self.blockSignals(False)
        self.setUpdatesEnabled(True)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() != 0:
            return
        row = item.row()
        if row < 0 or row >= len(self._events):
            return
        ev = self._events[row]
        key = _event_key(ev)
        if item.checkState() == Qt.CheckState.Checked:
            self._checked.add(key)
        else:
            self._checked.discard(key)
        self.checked_count_changed.emit(len(self._checked))

    def get_checked_events(self) -> list[dict]:
        return [ev for ev in self._all_events if _event_key(ev) in self._checked]

    def clear_checked(self):
        self._checked.clear()
        self.checked_count_changed.emit(0)
        self._apply_filter()

    def _on_selection_changed(self):
        rows = self.selectedItems()
        if not rows:
            self.event_selected.emit(None)
            return

        row = rows[0].row()
        if 0 <= row < len(self._events):
            self.event_selected.emit(self._events[row])
