from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.history import get_history, clear_history
from core.i18n import t


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("history_title"))
        self.setMinimumSize(900, 600)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        self._btn_refresh = QPushButton(t("history_refresh"))
        self._btn_refresh.clicked.connect(self._load_history)
        btn_layout.addWidget(self._btn_refresh)

        self._btn_clear = QPushButton(t("history_clear"))
        self._btn_clear.clicked.connect(self._clear_history)
        btn_layout.addWidget(self._btn_clear)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            t("history_col_date"), t("history_col_source"),
            t("history_col_event_id"), t("history_col_level"), t("history_col_provider"),
        ])
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSortingEnabled(True)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table, 1)

        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(250)
        self._detail.setStyleSheet(
            "background: #1A1A2E; border: 1px solid #2C3E50; border-radius: 4px; padding: 6px; color: #ECF0F1;"
        )
        layout.addWidget(self._detail)

    def _load_history(self):
        records = get_history(50)
        self._records = records
        self._table.setRowCount(len(records))
        for row, r in enumerate(records):
            self._table.setItem(row, 0, QTableWidgetItem(r.get("analyzed_at", "")))
            self._table.setItem(row, 1, QTableWidgetItem(r.get("source", "")))
            self._table.setItem(row, 2, QTableWidgetItem(str(r.get("event_id", ""))))
            self._table.setItem(row, 3, QTableWidgetItem(r.get("level", "")))
            self._table.setItem(row, 4, QTableWidgetItem(r.get("provider", "")))

    def _on_selection_changed(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        row = rows[0].row()
        if row < 0 or row >= len(self._records):
            return
        r = self._records[row]
        detail = (
            f"{t('history_detail_source', value=r.get('source', ''))}\n"
            f"{t('history_detail_event_id', value=r.get('event_id', ''))}\n"
            f"{t('history_detail_level', value=r.get('level', ''))}\n"
            f"{t('history_detail_provider', value=r.get('provider', ''))}\n"
            f"{t('history_detail_event_desc')}"
            f"{r.get('message', '')}\n"
            f"{t('history_detail_ai_analysis')}"
            f"{t('history_detail_what_is', value=r.get('ai_explanation', ''))}\n"
            f"{t('history_detail_severity', value=r.get('ai_severity', ''))}\n"
            f"{t('history_detail_what_to_do', value=r.get('ai_steps', ''))}\n"
            f"{t('history_detail_tip', value=r.get('ai_tip', ''))}\n"
        )
        self._detail.setPlainText(detail)

    def _clear_history(self):
        reply = QMessageBox.question(
            self, t("confirm_title"),
            t("confirm_clear_history"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_history()
            self._load_history()
            self._detail.clear()
