from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QScrollArea, QFrame,
    QListWidget, QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from core.i18n import t
import re


LEVEL_COLORS = {
    "Error": "#E74C3C",
    "Warning": "#F39C12",
}


class AiPanel(QWidget):
    analyze_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._event: dict | None = None
        self._results: list[dict | str] = []
        self._batch_events: list[dict] = []
        self._setup_ui()
        self._show_placeholder(t("ai_panel_select_event"))

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_content = QWidget()
        self._content_layout = QVBoxLayout(self._scroll_content)
        self._content_layout.setSpacing(6)
        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll, 1)

        self._btn_analyze = QPushButton(t("ai_panel_analyze"))
        self._btn_analyze.setEnabled(False)
        self._btn_analyze.clicked.connect(self.analyze_clicked.emit)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._btn_analyze, 1)

        self._btn_clear = QPushButton(t("ai_panel_clear"))
        self._btn_clear.setEnabled(False)
        self._btn_clear.clicked.connect(self.clear_clicked.emit)
        btn_row.addWidget(self._btn_clear)

        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._btn_cancel = QPushButton(t("ai_panel_cancel"))
        self._btn_cancel.setVisible(False)
        self._btn_cancel.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self._btn_cancel)

        self._btn_export = QPushButton(t("ai_panel_export"))
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._on_export)
        layout.addWidget(self._btn_export)

        self._result_list = QListWidget()
        self._result_list.setVisible(False)
        self._result_list.setMaximumHeight(250)
        self._result_list.currentRowChanged.connect(self._on_result_selected)
        layout.addWidget(self._result_list)

        self._analysis_widgets = []

    def _on_export(self):
        from PyQt6.QtWidgets import QFileDialog
        from core.exporter import export_txt, export_html

        if not self._results or not self._batch_events:
            return
        path, fmt = QFileDialog.getSaveFileName(
            self, t("export_dialog_title"), t("export_default_filename"),
            t("export_file_filter"),
        )
        if not path:
            return
        try:
            if path.endswith(".html"):
                export_html(path, self._results, self._batch_events)
            else:
                export_txt(path, self._results, self._batch_events)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, t("error_export"), str(e))

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._analysis_widgets = []

    def _make_field(self, label: str, value: str, color: str | None = None):
        lbl = QLabel(f"<b>{label}</b>")
        lbl.setStyleSheet("color: #3D5A80; font-size: 9pt;")
        val = QLabel(value)
        val.setStyleSheet(f"color: {color or '#ECF0F1'}; font-size: 10pt;")
        val.setWordWrap(True)
        return lbl, val

    def _show_placeholder(self, text: str):
        self._clear_content()
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #5D6D7E; font-size: 12pt;")
        self._content_layout.addStretch()
        self._content_layout.addWidget(lbl)
        self._content_layout.addStretch()

    def show_event(self, event: dict | None):
        self._clear_content()
        self._event = event
        self._btn_analyze.setEnabled(event is not None)

        if event is None:
            self._show_placeholder(t("ai_panel_select_event"))
            return

        color = LEVEL_COLORS.get(event["Level"], "#ECF0F1")

        rows = [
            (t("field_source"), event["SourceName"], None),
            (t("field_event_id"), str(event["EventID"]), None),
            (t("field_level"), event["Level"], color),
            (t("field_datetime"), event["TimeGenerated"].strftime("%Y-%m-%d %H:%M:%S"), None),
        ]

        for label, value, clr in rows:
            l, v = self._make_field(label, value, clr)
            self._content_layout.addWidget(l)
            self._content_layout.addWidget(v)

        self._content_layout.addSpacing(10)

        desc_lbl = QLabel(f"<b>{t('section_event_description')}</b>")
        desc_lbl.setStyleSheet("color: #3D5A80; font-size: 9pt;")

        msg = QTextEdit()
        msg.setReadOnly(True)
        msg.setPlainText(event["Message"])
        msg.setMaximumHeight(200)
        msg.setStyleSheet("background: #1A1A2E; border: 1px solid #2C3E50; border-radius: 4px; padding: 6px; color: #ECF0F1;")

        self._content_layout.addWidget(desc_lbl)
        self._content_layout.addWidget(msg)

        self._content_layout.addSpacing(10)

        ai_header = QLabel(f"<b>{t('section_ai_analysis')}</b>")
        ai_header.setStyleSheet("color: #3D5A80; font-size: 9pt;")
        self._content_layout.addWidget(ai_header)

        placeholder = QLabel(t("ai_panel_placeholder"))
        placeholder.setStyleSheet("color: #5D6D7E; font-size: 10pt; padding: 8px;")
        placeholder.setWordWrap(True)
        self._content_layout.addWidget(placeholder)
        self._analysis_widgets.append(placeholder)

        self._content_layout.addStretch()

    def show_analysis(self, result: dict | None, error: str | None = None):
        for w in self._analysis_widgets:
            w.deleteLater()
        self._analysis_widgets = []

        if error:
            v = QTextEdit()
            v.setReadOnly(True)
            escaped = error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            v.setHtml(f'<p style="color:#E74C3C; font-size:10pt;">{t("error_title")}:<br>{escaped}</p>')
            v.setStyleSheet("background: transparent; border: none; padding: 8px;")
            self._content_layout.insertWidget(self._content_layout.count() - 1, v)
            self._analysis_widgets.append(v)
            return

        if result is None:
            return

        section_config = [
            ("section_what_is", result.get("explanation", ""), None),
            ("section_is_serious", result.get("severity", ""),
             "#27AE60" if "nie" in result.get("severity", "").lower() else "#E74C3C"),
            ("section_what_to_do", result.get("steps", ""), None),
        ]

        for key, text, clr in section_config:
            title = t(key)
            h = QLabel(f"<b>{self._get_icon(key)} {title}</b>")
            h.setStyleSheet("color: #3D5A80; font-size: 10pt; margin-top: 6px;")
            self._content_layout.insertWidget(self._content_layout.count() - 1, h)
            self._analysis_widgets.append(h)

            v = QTextEdit()
            v.setReadOnly(True)
            v.setHtml(self._md_to_html(text))
            v.setMaximumHeight(120)
            v.setStyleSheet(
                "background: transparent; border: none; "
                f"color: {clr or '#ECF0F1'}; font-size: 10pt; padding: 2px 0;"
            )
            self._content_layout.insertWidget(self._content_layout.count() - 1, v)
            self._analysis_widgets.append(v)

        tip = result.get("tip")
        if tip:
            tip_key = "section_tip"
            ttl = QLabel(f"<b>{self._get_icon(tip_key)} {t(tip_key)}</b>")
            ttl.setStyleSheet("color: #3D5A80; font-size: 10pt; margin-top: 6px;")
            self._content_layout.insertWidget(self._content_layout.count() - 1, ttl)
            self._analysis_widgets.append(ttl)
            tv = QTextEdit()
            tv.setReadOnly(True)
            tv.setHtml(self._md_to_html(tip))
            tv.setMaximumHeight(80)
            tv.setStyleSheet(
                "background: transparent; border: none; "
                "color: #F39C12; font-size: 10pt; padding: 2px 0;"
            )
            self._content_layout.insertWidget(self._content_layout.count() - 1, tv)
            self._analysis_widgets.append(tv)

    def show_batch_analysis(self, results: list[dict | str], events: list[dict]):
        self._results = results
        self._batch_events = events
        self._result_list.clear()
        self._result_list.setVisible(True)
        self._btn_export.setEnabled(True)

        for i, ev in enumerate(events):
            src = ev.get("SourceName", "?")
            eid = ev.get("EventID", "?")
            level = ev.get("Level", "")
            r = results[i] if i < len(results) else None
            status = "OK" if isinstance(r, dict) and "error" not in r else "ERR"
            icon = "✅" if status == "OK" else "❌"
            self._result_list.addItem(f"{icon} [{level}] {src} | ID: {eid}")

    def set_batch_mode(self, active: bool, total: int = 0):
        self._btn_analyze.setVisible(not active)
        self._btn_cancel.setVisible(active)
        self._progress.setVisible(active)
        self._btn_export.setVisible(not active)
        if active:
            self._progress.setMaximum(total)
            self._progress.setValue(0)

    def update_batch_progress(self, current: int, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(current)

    def set_analyze_enabled(self, enabled: bool):
        self._btn_analyze.setEnabled(enabled)

    def show_checked_events(self, events: list[dict]):
        self._clear_content()
        self._event = None
        self._btn_analyze.setEnabled(bool(events))

        if not events:
            self._show_placeholder(t("ai_panel_select_checkboxes"))
            return

        header = QLabel(t("ai_panel_checked_count", count=len(events)))
        header.setStyleSheet("color: #3D5A80; font-size: 10pt;")
        self._content_layout.addWidget(header)

        for ev in events:
            color = LEVEL_COLORS.get(ev["Level"], "#ECF0F1")
            line = QLabel(
                f'<span style="color:{color};">[{ev["Level"]}]</span> '
                f'<b>{ev["SourceName"]}</b> | ID: {ev["EventID"]}'
            )
            line.setStyleSheet("color: #ECF0F1; font-size: 9pt; padding: 1px 0;")
            self._content_layout.addWidget(line)

        self._content_layout.addStretch()

    def _on_result_selected(self, row: int):
        if row < 0 or row >= len(self._results):
            return
        r = self._results[row]
        if isinstance(r, dict) and "error" not in r:
            self.show_analysis(r)
        else:
            err = r if isinstance(r, str) else r.get("error", t("error_unknown"))
            self.show_analysis(None, err)

    @staticmethod
    def _get_icon(section_key: str) -> str:
        icons = {"section_what_is": "🔍", "section_is_serious": "⚠️", "section_what_to_do": "🔧", "section_tip": "💡"}
        return icons.get(section_key, "")

    @staticmethod
    def _md_to_html(text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        parts = text.split("\n")
        html_parts = []
        for p in parts:
            p = p.strip()
            if not p:
                html_parts.append("<br>")
            elif p.startswith("- ") or p.startswith("* "):
                html_parts.append(f"&nbsp;&nbsp;• {p[2:].strip()}")
            else:
                html_parts.append(p)
        return "<br>".join(html_parts)
