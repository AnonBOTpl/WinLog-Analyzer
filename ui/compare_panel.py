from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.comparator import get_latest_analysis_snapshot, compare_events
from core.i18n import t

COLOR_NEW = QColor("#27AE60")
COLOR_RESOLVED = QColor("#7F8C8D")
COLOR_REPEATED = QColor("#F39C12")


class ComparePanel(QDialog):
    def __init__(self, current_events: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("compare_title"))
        self.setMinimumSize(1000, 600)
        self._current_events = current_events
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        previous = get_latest_analysis_snapshot()
        if not previous:
            layout.addWidget(QLabel(t("compare_empty_history")))
            return

        result = compare_events(self._current_events, previous)

        tabs = QTabWidget()

        tabs.addTab(self._make_table(result["new"], COLOR_NEW, "↑"), t("compare_tab_new"))
        tabs.addTab(self._make_table(result["resolved"], COLOR_RESOLVED, "↓", is_history=True), t("compare_tab_resolved"))
        tabs.addTab(self._make_all_table(result, previous), t("compare_tab_all"))

        layout.addWidget(tabs)

        summary = t("compare_summary",
            new=len(result['new']), resolved=len(result['resolved']),
            repeated=len(result['repeated']))
        lbl = QLabel(summary)
        lbl.setStyleSheet("color: #3D5A80; font-size: 10pt; padding: 4px;")
        layout.addWidget(lbl)

    def _make_table(self, events: list[dict], color, icon: str, is_history: bool = False):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        headers = ["", t("compare_col_datetime"), t("compare_col_source"), t("compare_col_event_id"), t("compare_col_description")]
        table = self._create_table(headers, len(events))

        for row, ev in enumerate(events):
            dt, src, eid, msg = self._event_data(ev, is_history)
            icon_item = QTableWidgetItem(icon)
            icon_item.setForeground(color)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, icon_item)
            table.setItem(row, 1, QTableWidgetItem(dt))
            table.setItem(row, 2, QTableWidgetItem(src))
            table.setItem(row, 3, QTableWidgetItem(eid))
            table.setItem(row, 4, QTableWidgetItem(msg))

        layout.addWidget(table)
        return widget

    def _make_all_table(self, result: dict, previous: list[dict]):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        headers = [t("compare_col_status"), t("compare_col_datetime"), t("compare_col_source"),
                   t("compare_col_event_id"), t("compare_col_description"), t("compare_col_previous")]
        total = len(result["new"]) + len(result["resolved"]) + len(result["repeated"])
        table = self._create_table(headers, total)

        row = 0
        for ev in result["new"]:
            dt, src, eid, msg = self._event_data(ev)
            self._set_row(table, row, t("compare_status_new"), COLOR_NEW, dt, src, eid, msg, t("compare_previous_none"))
            row += 1

        for ev in result["repeated"]:
            dt, src, eid, msg = self._event_data(ev)
            self._set_row(table, row, t("compare_status_repeated"), COLOR_REPEATED, dt, src, eid, msg, t("compare_previous_yes"))
            row += 1

        for r in result["resolved"]:
            dt, src, eid, msg = self._event_data(r, is_history=True)
            self._set_row(table, row, t("compare_status_resolved"), COLOR_RESOLVED, dt, src, eid, msg, t("compare_previous_yes"))
            row += 1

        layout.addWidget(table)
        return widget

    @staticmethod
    def _create_table(headers: list[str], row_count: int) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSortingEnabled(True)
        table.setRowCount(row_count)
        return table

    @staticmethod
    def _event_data(ev: dict, is_history: bool = False) -> tuple[str, str, str, str]:
        if is_history:
            dt = ev.get("analyzed_at", "")
            src = ev.get("source", "")
            eid = str(ev.get("event_id", ""))
            msg = ev.get("message", "")[:120]
        else:
            tg = ev.get("TimeGenerated")
            dt = tg.strftime("%Y-%m-%d %H:%M:%S") if hasattr(tg, "strftime") else str(tg or "")
            src = ev.get("SourceName", "")
            eid = str(ev.get("EventID", ""))
            msg = ev.get("Message", "")[:120]
        return dt, src, eid, msg

    @staticmethod
    def _set_row(table, row, status, color, dt, src, eid, msg, prev):
        s = QTableWidgetItem(status)
        s.setForeground(color)
        table.setItem(row, 0, s)
        table.setItem(row, 1, QTableWidgetItem(dt))
        table.setItem(row, 2, QTableWidgetItem(src))
        table.setItem(row, 3, QTableWidgetItem(eid))
        table.setItem(row, 4, QTableWidgetItem(msg))
        table.setItem(row, 5, QTableWidgetItem(prev))
