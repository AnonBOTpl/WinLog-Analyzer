# Changelog

## v2.2.0 (2026-06-24)

### Code Quality & Refactoring
- Removed embedded translations (`_ENGLISH`, `_POLISH`, `_EMBEDDED`) from `core/i18n.py` — translations now exclusively from JSON files
- Extracted shared table helpers (`_create_table`, `_event_data`, `_set_row`) in `compare_panel.py` — eliminated code duplication
- Removed unused `label` parameter from `_make_table()` and its callers
- Replaced `os.spawnl` with `subprocess.Popen` in `_restart_app()` for better portability
- Added full docstrings to all public functions in `core/` and `providers/` (14 files)

### Stability & Safety
- Added **QTimer timeouts** for all background workers:
  - LoadEventsWorker: 60s
  - AnalysisWorker: 120s
  - BatchAnalysisWorker: 120s per event
  - TestKeyWorker: 15s
  - ScanModelsWorker: 30s
- Added guard against multiple `LoadEventsWorker` instances on rapid Refresh clicks
- Added guard against `self._worker` overwrite in `_test_key()` and `_scan_models()`
- Added **SQLite indexes** (`idx_analyses_analyzed_at`, `idx_analyses_source_event`) for history query performance
- Added **300s TTL** to `_QUERYABLE_CACHE` — cache now expires and re-checks channels
- Added **10s timeout** for `_evt_render_xml` via `ThreadPoolExecutor` — prevents hangs on problematic events
- Added `atexit` cleanup for the render thread pool

### Dependency & Compatibility
- Lowered `requires-python` from `>=3.12` to `>=3.10` (all dependencies support 3.10)
- Removed unused `import win32evtlogutil` and `BATCH_SIZE_BYTES` from `core/log_reader.py`
- Removed dead code `get_events()` (old ReadEventLog API fallback)
- Removed duplicated `_on_export()` from `ui/main_window.py`

### Testing
- Added `tests/` directory with unit test suite
- `tests/test_base.py` — 15 tests for `system_prompt()`, `_build_prompt()`, `_parse_sections()`
- `tests/test_log_reader.py` — 24 tests for `_parse_iso_time()`, `_parse_event_xml()`, constants
- Added `test.bat` — one-click test runner with verbose output
- All **39 tests passing**

### Documentation
- Complete README rewrite: features, screenshots, installation, configuration, usage, testing, project structure
- Added GitHub link: `https://github.com/AnonBOTpl/WinLog-Analyzer`
- Updated `.gitignore` — added `test.bat` and `tests/__pycache__/` patterns

---

## v2.1.1 (2026-06-24)

### Changes
- Dropped PyInstaller / Nuitka packaging – app now runs via `uv run python main.py`
- `start.bat` – runs directly with `uv`, no .exe check
- `install.bat` – simplified to `uv venv` + `uv sync`, no build step
- Default language changed from Polish to English
- English and Polish translations embedded in `core/i18n.py` – no dependency on external JSON files at runtime
- `available_languages()` fallback scans `sys._MEIPASS` for locales in frozen mode; embedded dicts always available
- `_restart_app()` fixed for frozen/dev mode; uses `os._exit(0)` to avoid PyInstaller temp-dir warning
- New "Delete key" button in Settings (`keyring.delete_password`)

### Bug Fixes
- `core/i18n.py` – added missing `import sys` / `from pathlib import Path` causing `NameError` in frozen builds
- `core/paths.py` – reverted `_base_path()` to `sys.executable.parent`, removed over-engineered `_candidates()`
- Graceful handling when locale JSON files are missing (logs warning, uses embedded translations)

---

## v2.1.0 (2026-06-24)

### New Features
- Internationalization (i18n) – switch language PL/EN in Settings
- `core/i18n.py` – translation module with `load()`, `t()`, `available_languages()`
- `locales/en.json`, `locales/pl.json` – 113 translation keys each
- AI system prompt (`providers/base.py`) adapts to the selected language (response sections, field labels)
- All error messages in providers (4 × Gemini/Claude/OpenAI/Groq) via `t()`
- Language ComboBox in Settings + automatic restart on change
- `locales/CONTRIBUTING.md` – instructions for adding new languages

### Improvements
- Checkbox multi-select instead of Top N – persistent across filters, keyed by `(Source, EventID, TimeGenerated)`
- "Clear selection" button in AI panel
- Copyable AI responses (QLabel → QTextEdit readOnly)
- Markdown rendering in AI responses: `**bold**`, `*italic*`, `-`/`*` lists
- Background event loading (`LoadEventsWorker` in `QThread`) – no UI freeze on startup
- API timeout: 30s → 60s in all 4 providers
- Friendly 503 error message (API overload, suggests retrying)
- Windows source names (Application → Aplikacja etc.) via `t()` in both languages
- QSS for QLineEdit, QProgressBar, QListWidget, QScrollBar, QSpinBox
- Table performance: `setUpdatesEnabled(False)` + `blockSignals(True)` during rebuild

### Bug Fixes
- Level mapping: Evt Level=2 → "Error", Level=3 → "Warning" (Evt API)
- `_compute_source_counts()` uses `EVT_ERROR` constant instead of magic value
- BUG-01: Removed duplicate `get_all_sources()` in `core/log_reader.py`
- BUG-02: `_load_events()` moved to `LoadEventsWorker(QThread)` – UI no longer blocks
- BUG-04: `ScanModelsWorker` – added `self._worker = None` in `_on_scan_finished`
- BUG-05: "Critical" filter now shows Error(2)+Critical(1) instead of just Critical(1)
- BUG-06: `comparator.py` uses public `get_connection()` instead of `_get_conn`
- BUG-07: Changing provider in settings now resets the model list
- Signal `pyqtSignal(dict)` → `pyqtSignal(object)` – no crash on `emit(None)`

---

## v2.0.0 (2026-06-24)

### New AI Providers
- `providers/base.py` – abstract `AIProvider` class with `_build_prompt()`, `_parse_sections()`
- `providers/anthropic.py` – Claude API (claude-haiku-4-5)
- `providers/openai.py` – OpenAI (gpt-4o-mini)
- `providers/groq.py` – Groq (llama-3.1-8b-instant)
- `providers/gemini.py` – refactored to inherit from `AIProvider`
- `core/ai_client.py` – provider aggregator: `get_provider()`, `analyze_event()`, `validate_key()`, `list_models()`
- Shared system prompt, 60s timeout, 503 handling

### Batch Analysis
- `BatchAnalysisWorker(QThread)` – sequential requests, 1s pause between calls
- Progress bar in AI panel (`x / N analyzed`)
- "Cancel" button – stops the analysis
- Result list (QListWidget) – click to show details
- Single event error does not abort the entire batch

### Report Export
- `core/exporter.py` – `export_txt()` and `export_html()`
- HTML with dark theme (#1A1A2E, #ECF0F1)
- "Export" button in AI panel after batch analysis completes

### Analysis History
- `core/history.py` – SQLite database `data/winlog_history.db`
- Functions: `save_analysis()`, `get_history()`, `clear_history()`
- `ui/history_dialog.py` – table with Date/Source/Event ID/Level/Provider columns
- Read-only QTextEdit detail view on row click
- Auto-save after every analysis (single and batch)

### Search & Filter
- QLineEdit "Search..." above table (real-time, case-insensitive)
- Column filter ComboBox: All / Source / Event ID / Description
- Status bar: "X / Y events"

### Analysis Comparison
- `core/comparator.py` – compare current events with SQLite history
- `ui/compare_panel.py` – tabs: New / Resolved / All
- Color coding: green (new), gray (resolved), yellow (repeated)

### GitHub Releases
- `scripts/release.ps1` – build → zip → gh release upload
- `scripts/CHANGELOG.md` – change documentation

### PyInstaller Packaging
- `winlog_analyzer.spec` – one-folder, windowed, hidden imports for pywin32/keyring
- `install.bat` – fresh install (without UV, without venv)
- `start.bat` – launches .exe or falls back to `uv run python main.py`
- `build.bat` – quick rebuild
- `scripts/png2ico.py` – PNG → ICO conversion
- `pyproject.toml` v2.0.0, optional-dependencies build with pyinstaller>=6

### Icon & Paths
- `app.setWindowIcon(QIcon("ikona.png"))` – icon in titlebar and taskbar
- `core/paths.py` – `resource_path()` for bundled files, `data_file()` for `%APPDATA%`
- Frozen (PyInstaller) and dev (uv run) mode support

---

## v1.0.0 (2026-06-23)

### Project & Structure
- Project initialization with UV, Python 3.12
- Directory structure: `core/`, `ui/`, `providers/`, `config/`
- `pyproject.toml` – dependencies: PyQt6, pywin32, requests, keyring, tzdata
- `main.py` – entry point with Fusion style and dark theme
- `.gitignore` – venv, `__pycache__`, dist/, build/

### Windows Event Log Reading
- `core/log_reader.py` – `win32evtlog` API (EvtQuery), 1193 channels
- `get_all_sources()` – dynamic channel enumeration via `EvtOpenChannelEnum`
- `get_events_from_sources()` – event aggregation from all channels
- Channel filtering: skips Analytic/Debug/Diagnostic/Performance/Trace
- UTC → Europe/Warsaw timezone conversion via `zoneinfo`
- `_parse_event_xml()` – extracts SourceName, EventID, Level, Message, TimeGenerated

### Event Filtering
- `core/log_filter.py` – filtering by EventType (Error/Warning), date, source
- `filter_events()` – level + time range + source

### User Interface
- `ui/main_window.py` – QMainWindow with toolbar, splitter (table 60% / AI panel 40%), status bar
- `ui/log_table.py` – QTableWidget with Date/Time, Level, Source, Event ID, Description columns
- Color coding: Error (#E74C3C), Warning (#F39C12), background (#16213E)
- `ui/ai_panel.py` – event detail panel with Source, Event ID, Level, Date, Description fields
- Navigation tree (NavTree) – All, Critical, Windows Logs, Applications & Services
- Column sorting, row selection

### Google Gemini Integration
- `providers/gemini.py` – `GeminiProvider.analyze()`, `validate_api_key()`, `list_models()`
- Default model: gemini-2.5-flash
- System prompt: Windows expert, responses in Polish
- Response structure: 🔍 What is this / ⚠️ Is it serious / 🔧 What to do / 💡 Tip
- `AnalysisWorker(QThread)` – AI queries in background without UI blocking
- `BatchAnalysisWorker` – skeleton preparation

### Settings
- `ui/settings_dialog.py` – provider selection, API key (keyring, Windows Credential Manager)
- Model scanning from API, key testing
- Model ComboBox, saved to `config/settings.json`

### Dark Theme
- `ui/styles.qss` – dark theme: #1A1A2E, #16213E, #ECF0F1
- Font: Segoe UI, 10pt
- Styling for table, buttons, text fields

### Time Filter
- Toolbar ComboBox: 24h / 7d / 30d / All / Custom range
- QDateEdit for custom date range
- In-memory filtering on already fetched data
