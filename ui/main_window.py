import sys, os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout,
    QToolBar, QComboBox, QPushButton, QLabel,
    QStatusBar, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QDialog, QHBoxLayout, QDateEdit, QDialogButtonBox,
    QLineEdit, QApplication,
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from core.log_filter import filter_events
from core.history import save_analysis
from core.i18n import t

# Evt API Level values: 2=Error, 3=Warning
EVT_ERROR = 2
EVT_WARNING = 3
from core.analysis_worker import LoadEventsWorker, AnalysisWorker, BatchAnalysisWorker
from ui.log_table import LogTable
from ui.ai_panel import AiPanel
from ui.settings_dialog import SettingsDialog, load_settings, get_api_key
from ui.history_dialog import HistoryDialog
from ui.compare_panel import ComparePanel

WARSAW_TZ = ZoneInfo("Europe/Warsaw")

SOURCE_DISPLAY_KEYS = {
    "Application": "source_application",
    "Security": "source_security",
    "Setup": "source_setup",
    "System": "source_system",
    "Microsoft-Windows-PowerShell/Operational": "source_powershell",
    "Microsoft-Windows-Kernel-Power/Operational": "source_kernel_power",
    "Microsoft-Windows-WMI-Activity/Operational": "source_wmi_activity",
    "Hardware Events": "source_hardware_events",
}


class NavTree(QTreeWidget):
    source_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setRootIsDecorated(True)
        self.itemClicked.connect(self._on_item_clicked)
        self._source_items: dict[str, QTreeWidgetItem] = {}

    def build_tree(self, sources: list[str], counts: dict[str, int]):
        self.clear()
        self._source_items = {}

        total = counts.get("__all__", 0)
        critical = counts.get("__critical__", 0)

        self.item_all = QTreeWidgetItem([t("nav_all_errors", count=total)])
        self.item_all.setData(0, Qt.ItemDataRole.UserRole, "all")
        self.addTopLevelItem(self.item_all)

        self.item_critical = QTreeWidgetItem([t("nav_critical", count=critical)])
        self.item_critical.setData(0, Qt.ItemDataRole.UserRole, "critical")
        self.addTopLevelItem(self.item_critical)

        system_sources = [s for s in sources if s in ("Application", "Security", "Setup", "System")]
        service_sources = [s for s in sources if s not in ("Application", "Security", "Setup", "System")]

        cat_system = QTreeWidgetItem([t("nav_windows_logs")])
        cat_system.setFlags(cat_system.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        font = cat_system.font(0)
        font.setBold(True)
        cat_system.setFont(0, font)
        self.addTopLevelItem(cat_system)

        has_system = False
        for src in system_sources:
            c = counts.get(src, 0)
            if c == 0:
                continue
            has_system = True
            display_key = SOURCE_DISPLAY_KEYS.get(src)
            display = t(display_key, default=src) if display_key else src
            item = QTreeWidgetItem([f"{display}  [{c}]"])
            item.setData(0, Qt.ItemDataRole.UserRole, src)
            cat_system.addChild(item)
            self._source_items[src] = item
        if not has_system:
            cat_system.setHidden(True)

        cat_services = QTreeWidgetItem([t("nav_apps_services")])
        cat_services.setFlags(cat_services.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        cat_services.setFont(0, font)
        self.addTopLevelItem(cat_services)

        has_service = False
        for src in service_sources:
            c = counts.get(src, 0)
            if c == 0:
                continue
            has_service = True
            display_key = SOURCE_DISPLAY_KEYS.get(src)
            display = t(display_key, default=src) if display_key else src
            item = QTreeWidgetItem([f"{display}  [{c}]"])
            item.setData(0, Qt.ItemDataRole.UserRole, src)
            cat_services.addChild(item)
            self._source_items[src] = item
        if not has_service:
            cat_services.setHidden(True)

        self.expandAll()
        self.setCurrentItem(self.item_all)

    def update_count(self, source: str, count: int):
        if source == "__all__":
            self.item_all.setText(0, t("nav_all_errors", count=count))
        elif source == "__critical__":
            self.item_critical.setText(0, t("nav_critical", count=count))
        elif source in self._source_items:
            display_key = SOURCE_DISPLAY_KEYS.get(source)
            display = t(display_key, default=source) if display_key else source
            self._source_items[source].setText(0, f"{display}  [{count}]")

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        source = item.data(0, Qt.ItemDataRole.UserRole)
        if source is not None:
            self.source_selected.emit(source)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._events_raw = []
        self._events_filtered = []
        self._current_selection: dict | None = None
        self._worker: AnalysisWorker | None = None
        self._batch_worker: BatchAnalysisWorker | None = None
        self._batch_results: list = []
        self._batch_events: list = []
        self._all_sources: list[str] = []
        self._load_worker: LoadEventsWorker | None = None

        self._settings = load_settings()
        self._provider_name = self._settings.get("selected_provider", "gemini")
        self._model_name = self._settings.get("selected_model", "gemini-2.5-flash")

        self.setWindowTitle("WinLog Analyzer")
        self.setMinimumSize(1400, 700)

        self._setup_toolbar()
        self._setup_central()
        self._setup_statusbar()
        self._apply_styles()

        self._load_events()

    def _setup_toolbar(self):
        toolbar = QToolBar(t("toolbar_main"))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        title = QLabel(f"  {t('app_title')}  ")
        toolbar.addWidget(title)

        self.btn_refresh = QPushButton(t("toolbar_refresh"))
        self.btn_refresh.clicked.connect(self._load_events)
        toolbar.addWidget(self.btn_refresh)

        toolbar.addSeparator()

        self.cmb_level = QComboBox()
        self.cmb_level.addItems([
            t("toolbar_level_errors_warnings"),
            t("toolbar_level_errors_only"),
            t("toolbar_level_warnings_only"),
        ])
        self.cmb_level.currentIndexChanged.connect(self._on_level_filter_changed)
        toolbar.addWidget(self.cmb_level)

        toolbar.addSeparator()

        self.cmb_time = QComboBox()
        self.cmb_time.addItems([
            t("toolbar_time_24h"),
            t("toolbar_time_7d"),
            t("toolbar_time_30d"),
            t("toolbar_time_all"),
            t("toolbar_time_custom"),
        ])
        self.cmb_time.currentIndexChanged.connect(self._on_time_filter_changed)
        toolbar.addWidget(self.cmb_time)

        toolbar.addSeparator()

        self.btn_settings = QPushButton(t("toolbar_settings"))
        self.btn_settings.clicked.connect(self._open_settings)
        toolbar.addWidget(self.btn_settings)

        toolbar.addSeparator()

        self.btn_history = QPushButton(t("toolbar_history"))
        self.btn_history.clicked.connect(self._on_show_history)
        toolbar.addWidget(self.btn_history)

        self.btn_compare = QPushButton(t("toolbar_compare"))
        self.btn_compare.clicked.connect(self._on_show_compare)
        toolbar.addWidget(self.btn_compare)

    def _setup_central(self):
        outer = QSplitter(Qt.Orientation.Horizontal)

        self.nav_tree = NavTree()
        self.nav_tree.setMinimumWidth(180)
        self.nav_tree.source_selected.connect(self._on_nav_selected)

        mid_splitter = QSplitter(Qt.Orientation.Horizontal)

        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(4)

        search_bar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(t("table_search_placeholder"))
        self.txt_search.textChanged.connect(self._on_search_changed)
        search_bar.addWidget(self.txt_search, 1)

        self.cmb_search_col = QComboBox()
        self.cmb_search_col.addItems([
            t("table_search_all"), t("table_search_source"),
            t("table_search_event_id"), t("table_search_description"),
        ])
        self.cmb_search_col.currentIndexChanged.connect(self._on_search_changed)
        search_bar.addWidget(self.cmb_search_col)
        table_layout.addLayout(search_bar)

        self.log_table = LogTable()
        self.log_table.event_selected.connect(self._on_event_selected)
        self.log_table.checked_count_changed.connect(self._on_checked_count_changed)
        table_layout.addWidget(self.log_table, 1)

        self.ai_panel = AiPanel()
        self.ai_panel.analyze_clicked.connect(self._on_analyze_clicked)
        self.ai_panel.cancel_clicked.connect(self._on_cancel_batch)
        self.ai_panel.clear_clicked.connect(self._on_clear_checked)

        mid_splitter.addWidget(table_container)
        mid_splitter.addWidget(self.ai_panel)
        mid_splitter.setStretchFactor(0, 6)
        mid_splitter.setStretchFactor(1, 4)

        outer.addWidget(self.nav_tree)
        outer.addWidget(mid_splitter)
        outer.setStretchFactor(0, 0)
        outer.setStretchFactor(1, 1)

        self.setCentralWidget(outer)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.lbl_event_count = QLabel(t("status_events", visible=0, total=0))
        self.lbl_provider = QLabel(t("status_provider", provider=self._provider_name.capitalize()))
        self.lbl_status = QLabel(t("status_ready"))
        self.status.addWidget(self.lbl_event_count)
        self.status.addPermanentWidget(self.lbl_provider)
        self.status.addPermanentWidget(self.lbl_status)

    def _apply_styles(self):
        qss_path = Path(__file__).resolve().parent.parent / "ui" / "styles.qss"
        with open(qss_path, encoding="utf-8") as f:
            self.setStyleSheet(f.read())

    def _load_events(self):
        if self._load_worker is not None:
            return

        self.lbl_status.setText(t("status_loading"))
        self.btn_refresh.setEnabled(False)

        self._load_worker = LoadEventsWorker(max_events=10000)
        self._load_worker.finished.connect(self._on_load_finished)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.start()

        self._load_timer = QTimer.singleShot(60000, self._on_load_timeout)

    def _on_load_finished(self, sources: list[str], events: list[dict]):
        self._all_sources = sources
        self._events_raw = events
        self._apply_filters()
        self._update_nav_tree()
        self.btn_refresh.setEnabled(True)
        self.lbl_status.setText(t("status_ready"))
        self._load_worker = None

    def _on_load_error(self, msg: str):
        QMessageBox.warning(self, t("error_title"), t("error_loading_events", error=msg))
        self.btn_refresh.setEnabled(True)
        self.lbl_status.setText(t("status_load_error"))
        self._load_worker = None

    def _on_load_timeout(self):
        if self._load_worker is not None:
            self._load_worker.terminate()
            self._load_worker = None
            self.btn_refresh.setEnabled(True)
            self.lbl_status.setText(t("status_load_error"))

    def _apply_filters(self):
        idx = self.cmb_level.currentIndex()
        levels = [[EVT_ERROR, EVT_WARNING], [EVT_ERROR], [EVT_WARNING]][idx]
        self._events_filtered = filter_events(self._events_raw, levels=levels)
        self.log_table.set_events(self._events_filtered)
        self._update_event_count()

    def _compute_source_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ev in self._events_filtered:
            src = ev.get("LogSource", "")
            counts[src] = counts.get(src, 0) + 1
        counts["__all__"] = len(self._events_filtered)
        counts["__critical__"] = sum(1 for e in self._events_filtered if e.get("EventType") == EVT_ERROR)
        return counts

    def _update_nav_tree(self):
        counts = self._compute_source_counts()
        self.nav_tree.build_tree(self._all_sources, counts)

    def _on_nav_selected(self, source: str):
        self.log_table.filter_by_source(source)
        self._update_event_count()
        self.ai_panel.show_checked_events(self.log_table.get_checked_events())

    def _on_search_changed(self):
        self.log_table.set_search_filter(
            self.txt_search.text(),
            column=self.cmb_search_col.currentIndex(),
        )
        self._update_event_count()

    def _update_event_count(self):
        visible = self.log_table.rowCount()
        total = len(self._events_filtered) if self._events_filtered else len(self._events_raw)
        self.lbl_event_count.setText(t("status_events", visible=visible, total=total))

    def _on_level_filter_changed(self, index: int):
        self._apply_filters()
        self._update_nav_tree()

    def _open_settings(self):
        old_lang = self._settings.get("language", "en")
        dialog = SettingsDialog(self)
        if dialog.exec():
            self._settings = load_settings()
            self._provider_name = self._settings.get("selected_provider", "gemini")
            self._model_name = self._settings.get("selected_model", "gemini-2.5-flash")
            self.lbl_provider.setText(t("status_provider", provider=self._provider_name.capitalize()))
            new_lang = self._settings.get("language", "en")
            if new_lang != old_lang:
                self._restart_app()

    def _restart_app(self):
        import subprocess
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable])
        else:
            script = Path(__file__).resolve().parent.parent / "main.py"
            subprocess.Popen([sys.executable, str(script)])
        os._exit(0)

    def _on_time_filter_changed(self, index: int):
        if index < 0:
            return

        now = datetime.now(WARSAW_TZ)
        date_from = None
        date_to = None

        if index == 0:
            date_from = now - timedelta(hours=24)
        elif index == 1:
            date_from = now - timedelta(days=7)
        elif index == 2:
            date_from = now - timedelta(days=30)
        elif index == 3:
            pass
        elif index == 4:
            range_result = self._show_date_range_dialog()
            if range_result is None:
                self.cmb_time.setCurrentIndex(0)
                return
            date_from, date_to = range_result

        idx = self.cmb_level.currentIndex()
        levels = [[EVT_ERROR, EVT_WARNING], [EVT_ERROR], [EVT_WARNING]][idx]
        self._events_filtered = filter_events(
            self._events_raw,
            levels=levels,
            date_from=date_from,
            date_to=date_to,
        )
        self.log_table.set_events(self._events_filtered)
        self._update_event_count()
        self._update_nav_tree()

    def _show_date_range_dialog(self) -> tuple | None:
        dialog = QDialog(self)
        dialog.setWindowTitle(t("dialog_date_title"))
        dialog.setMinimumWidth(350)
        layout = QVBoxLayout(dialog)

        now = datetime.now(WARSAW_TZ)

        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel(t("dialog_date_from")))
        dt_from = QDateEdit()
        dt_from.setCalendarPopup(True)
        dt_from.setDate(QDate(now.year, now.month, now.day))
        dt_from.setDisplayFormat("yyyy-MM-dd")
        from_layout.addWidget(dt_from)

        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel(t("dialog_date_to")))
        dt_to = QDateEdit()
        dt_to.setCalendarPopup(True)
        dt_to.setDate(QDate(now.year, now.month, now.day))
        dt_to.setDisplayFormat("yyyy-MM-dd")
        to_layout.addWidget(dt_to)

        layout.addLayout(from_layout)
        layout.addLayout(to_layout)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.button(QDialogButtonBox.StandardButton.Ok).setText(t("dialog_ok"))
        btn_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t("dialog_cancel"))
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        qd_from = dt_from.date()
        qd_to = dt_to.date()
        date_from = datetime(qd_from.year(), qd_from.month(), qd_from.day(), tzinfo=WARSAW_TZ)
        date_to = datetime(qd_to.year(), qd_to.month(), qd_to.day(), 23, 59, 59, tzinfo=WARSAW_TZ)
        return date_from, date_to

    def _on_event_selected(self, event: dict | None):
        self._current_selection = event
        if self.log_table.get_checked_events():
            self.ai_panel.show_checked_events(self.log_table.get_checked_events())
        else:
            self.ai_panel.show_event(event)

    def _on_checked_count_changed(self, count: int):
        self.ai_panel.set_analyze_enabled(count > 0 or self._current_selection is not None)
        self.ai_panel._btn_clear.setEnabled(count > 0)
        if count > 0:
            self.ai_panel.show_checked_events(self.log_table.get_checked_events())
        elif self._current_selection:
            self.ai_panel.show_event(self._current_selection)
        else:
            self.ai_panel.show_event(None)

    def _on_clear_checked(self):
        self.log_table.clear_checked()

    def _on_analyze_clicked(self):
        api_key = get_api_key(self._provider_name)
        if not api_key:
            QMessageBox.warning(
                self, t("error_no_api_key_title"),
                t("error_no_api_key_text", provider=self._provider_name.capitalize()),
            )
            return

        checked = self.log_table.get_checked_events()
        if checked:
            self._start_batch(checked)
        elif self._current_selection:
            self.lbl_status.setText(t("status_analyzing"))
            self.ai_panel.show_analysis(None, t("status_analyzing"))
            self._worker = AnalysisWorker(
                provider_name=self._provider_name,
                api_key=api_key,
                model=self._model_name,
                event=self._current_selection,
            )
            self._worker.finished.connect(self._on_analysis_finished)
            self._worker.error.connect(self._on_analysis_error)
            self._worker.start()
            self._analysis_timer = QTimer.singleShot(120000, self._on_analysis_timeout)
        else:
            QMessageBox.information(self, t("msg_no_events_title"), t("msg_select_event"))

    def _start_batch(self, events: list[dict]):
        api_key = get_api_key(self._provider_name)
        if not api_key:
            QMessageBox.warning(self, t("error_no_api_key_title"), t("error_configure_api_key"))
            return

        n = len(events)
        self.ai_panel.set_batch_mode(True, n)
        self.lbl_status.setText(t("status_batch_progress", current=0, total=n))
        self._batch_results = []
        self._batch_events = events

        self._batch_worker = BatchAnalysisWorker(
            provider_name=self._provider_name,
            api_key=api_key,
            model=self._model_name,
            events=events,
        )
        self._batch_worker.progress.connect(self._on_batch_progress)
        self._batch_worker.event_done.connect(self._on_batch_event_done)
        self._batch_worker.event_error.connect(self._on_batch_event_error)
        self._batch_worker.finished.connect(self._on_batch_finished)
        self._batch_worker.start()

        timeout_ms = max(120000, n * 120000)
        self._batch_timer = QTimer.singleShot(timeout_ms, self._on_batch_timeout)

    def _on_analysis_finished(self, result: dict):
        self.ai_panel.show_analysis(result)
        self.lbl_status.setText(t("status_analyzed"))
        if self._current_selection:
            save_analysis(self._current_selection, result, self._provider_name)
        self._worker = None

    def _on_analysis_error(self, msg: str):
        self.ai_panel.show_analysis(None, msg)
        self.lbl_status.setText(t("status_error"))
        self._worker = None

    def _on_analysis_timeout(self):
        if self._worker is not None:
            self._worker.terminate()
            self._worker = None
            self.ai_panel.show_analysis(None, t("error_timeout", timeout=120))
            self.lbl_status.setText(t("status_error"))

    def _on_cancel_batch(self):
        if self._batch_worker:
            self._batch_worker.cancel()

    def _on_batch_progress(self, current: int, total: int):
        self.ai_panel.update_batch_progress(current, total)
        self.lbl_status.setText(t("status_batch_progress", current=current, total=total))

    def _on_batch_event_done(self, idx: int, result: dict):
        while len(self._batch_results) <= idx:
            self._batch_results.append(None)
        self._batch_results[idx] = result
        if idx < len(self._batch_events):
            save_analysis(self._batch_events[idx], result, self._provider_name)

    def _on_batch_event_error(self, idx: int, error: str):
        while len(self._batch_results) <= idx:
            self._batch_results.append(None)
        self._batch_results[idx] = error

    def _on_batch_finished(self):
        self.ai_panel.set_batch_mode(False)
        self.ai_panel.show_batch_analysis(self._batch_results, self._batch_events)
        self.lbl_status.setText(t("status_analyzed"))
        self.log_table.clear_checked()
        self._batch_worker = None

    def _on_batch_timeout(self):
        if self._batch_worker is not None:
            self._batch_worker.cancel()
            self._batch_worker.terminate()
            self._batch_worker = None
            self.ai_panel.set_batch_mode(False)
            self.lbl_status.setText(t("status_error"))



    def _on_show_history(self):
        dialog = HistoryDialog(self)
        dialog.exec()

    def _on_show_compare(self):
        if not self._events_filtered:
            QMessageBox.information(self, t("compare_title"), t("msg_no_events_compare"))
            return
        dialog = ComparePanel(self._events_filtered, self)
        dialog.exec()
