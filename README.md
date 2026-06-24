<div align="center">

# 🔍 WinLog Analyzer

**Windows Event Log Analyzer with AI-Powered Analysis**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.8%2B-41CD52?style=flat&logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)

[Features](#features) • [Installation](#installation) • [Configuration](#configuration) • [Usage](#usage) • [Testing](#testing) • [Project Structure](#project-structure)

---

</div>

## 📋 Overview

**WinLog Analyzer** is a desktop application for Windows that reads, filters, and analyzes Windows Event Logs with the help of AI. It supports **4 AI providers** (Google Gemini, Claude, OpenAI, Groq) and offers a modern dark-themed interface built with PyQt6.

The application helps system administrators and IT professionals quickly identify issues by providing AI-powered explanations, severity assessments, and remediation steps for Windows events.

<img width="1920" height="1031" alt="{948BD248-D410-4D91-BEAB-98D80280E098}" src="https://github.com/user-attachments/assets/5488dfd7-64c8-40a6-8658-807f42c8872c" />


## ✨ Features

### 📊 Event Log Reading
- Reads from all **1193+ Windows Event Log channels** (System, Application, Security, Setup, PowerShell, etc.)
- Smart channel filtering — skips Analytic/Debug/Diagnostic/Performance/Trace channels
- Timezone conversion to Europe/Warsaw
- Background loading — no UI freeze during startup
- 10-second timeout per XML render to avoid hanging on problematic events
- **Search events** in real-time across all columns or filter by Source, Event ID, or Description

### 🔬 AI-Powered Analysis
- **4 providers**: Google Gemini, Claude (Anthropic), OpenAI, Groq
- Single event analysis or **batch analysis** (with progress bar and cancel button)
- Structured responses with emoji markers:
  - 🔍 What is this
  - ⚠️ Is it serious
  - 🔧 What to do
  - 💡 Tip
- Auto-save analysis history to SQLite database

### 🎛️ Filtering & Navigation
- Level filter: Errors & Warnings / Errors Only / Warnings Only
- Time filter: Last 24h / 7d / 30d / All / Custom date range
- Navigation tree: All, Critical, Windows Logs, Applications & Services
- Real-time search with column selection
- Multi-select with persistent checkboxes

### 📈 Comparison & History
- **Analysis history** — browse all past analyses with detailed view
- **Comparison mode** — compare current events against history (New / Resolved / Repeated)
- Color-coded: green (new), gray (resolved), yellow (repeated)

### 📤 Export
- Export reports to **HTML** (dark-themed) or **TXT**
- Batch export after multi-event analysis

### 🌐 Internationalization
- English and Polish translations included
- Easy to add new languages (see `locales/CONTRIBUTING.md`)
- AI responses match the selected language

### 🎨 Dark Theme
- Modern dark interface (#1A1A2E, #16213E, #ECF0F1)
- Custom QSS stylesheet for all widgets
- Color-coded event levels: Error (red), Warning (orange)

## 🚀 Installation

### Prerequisites
- **Windows** (required for Windows Event Log API)
- **Python 3.10 or higher**
- **UV** (fast Python package manager)

### Quick Install

```powershell
# Clone the repository
git clone https://github.com/AnonBOTpl/WinLog-Analyzer.git
cd WinLog-Analyzer

# Run the installer
install.bat
```

Or manually:

```powershell
uv venv
uv sync
```

### Running

```powershell
start.bat
```

Or directly:

```powershell
uv run python main.py
```

## ⚙️ Configuration

### AI Provider Setup

1. Open **Settings** from the toolbar
2. Select your AI provider:
   - **Google Gemini** — Get your free API key at [Google AI Studio](https://aistudio.google.com/)
   - **Claude (Anthropic)** — Get your API key at [console.anthropic.com](https://console.anthropic.com/)
   - **OpenAI** — Get your API key at [platform.openai.com](https://platform.openai.com/)
   - **Groq** — Get your free API key at [console.groq.com](https://console.groq.com/)
3. Enter your API key and click **Save key** (stored securely in Windows Credential Manager)
4. Click **Test key** to verify
5. Click **Scan models** to fetch available models
6. Select a model and click **OK**

### Language

Change the language in **Settings → Language**. The application will restart automatically.

## 🎮 Usage

### Basic Workflow

1. Launch the application — events load automatically
2. Use the **navigation tree** on the left to filter by source
3. Use **level** and **time** filters in the toolbar
4. **Search** for specific text using the search bar above the table
5. Click an event to view details in the AI panel
6. Click **Analyze** to get an AI-powered analysis
7. For multiple events, **check the boxes** and click **Analyze**

### Search

The search bar supports real-time, case-insensitive filtering:

- **All columns** — searches across Source, Event ID, Level, and Description
- **Source** — filter by event source
- **Event ID** — filter by event ID number
- **Description** — filter by event message text

### Batch Analysis

1. Check the boxes next to events you want to analyze
2. Click **Analyze** — a progress bar shows the status
3. Click individual results in the list to view details
4. Click **Export report** to save as HTML or TXT

### Comparison

1. Run some AI analyses first (history is needed)
2. Click **Compare** in the toolbar
3. View tabs: **New** events, **Resolved** events, **All** events

## 🧪 Testing

Run the test suite:

```powershell
test.bat
```

Or manually:

```powershell
uv run python -m unittest discover tests/ -v
```

Current test coverage: **39 tests** covering:
- `core/log_reader.py` — XML parsing, time conversion, constants
- `providers/base.py` — system prompt, event prompt builder, section parsing

## 📁 Project Structure

```
WinLog Analyzer/
├── main.py                  # Entry point
├── pyproject.toml           # Dependencies and metadata
├── install.bat              # One-click installer
├── start.bat                # Launcher
├── test.bat                 # Test runner
├── .python-version          # Python version for uv
│
├── core/                    # Business logic
│   ├── log_reader.py        # Windows Event Log reader (win32evtlog API)
│   ├── log_filter.py        # Event filtering (level, date, source)
│   ├── analysis_worker.py   # Background QThread workers
│   ├── ai_client.py         # AI provider aggregator
│   ├── exporter.py          # Report export (TXT/HTML)
│   ├── history.py           # SQLite analysis history
│   ├── comparator.py        # Event comparison engine
│   ├── i18n.py              # Internationalization
│   └── paths.py             # File path resolution
│
├── providers/               # AI provider integrations
│   ├── base.py              # Abstract AIProvider class
│   ├── gemini.py            # Google Gemini
│   ├── anthropic.py         # Claude (Anthropic)
│   ├── openai.py            # OpenAI
│   └── groq.py              # Groq
│
├── ui/                      # PyQt6 user interface
│   ├── main_window.py       # Main window (toolbar, splitter, status bar)
│   ├── log_table.py         # Event log table with checkboxes
│   ├── ai_panel.py          # AI analysis panel
│   ├── settings_dialog.py   # Settings dialog
│   ├── history_dialog.py    # Analysis history
│   ├── compare_panel.py     # Event comparison
│   └── styles.qss           # Dark theme stylesheet
│
├── locales/                 # Translation files
│   ├── en.json              # English
│   ├── pl.json              # Polish
│   └── CONTRIBUTING.md      # Guide for adding languages
│
├── tests/                   # Unit tests
│   ├── test_base.py         # Tests for providers/base.py
│   └── test_log_reader.py   # Tests for core/log_reader.py
│
└── scripts/
    └── png2ico.py           # PNG → ICO conversion utility
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.10+ |
| **UI Framework** | PyQt6 |
| **Event Log API** | pywin32 (win32evtlog) |
| **AI Providers** | Google Gemini, Claude, OpenAI, Groq |
| **Database** | SQLite (via history module) |
| **Key Storage** | Windows Credential Manager (keyring) |
| **HTTP** | requests |
| **Timezone** | tzdata |
| **Package Manager** | uv |

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Add a new language** — see `locales/CONTRIBUTING.md`
2. **Add a new AI provider** — implement `AIProvider` from `providers/base.py`
3. **Write tests** — improve coverage in `tests/`
4. **Report bugs** — open an issue on GitHub
5. **Suggest features** — open a discussion

## 📄 License

This project is open source. See the LICENSE file for details.

---

<div align="center">

**Made with ❤️ by [AnonBOTpl](https://github.com/AnonBOTpl)**

[Report Bug](https://github.com/AnonBOTpl/WinLog-Analyzer/issues) • [Request Feature](https://github.com/AnonBOTpl/WinLog-Analyzer/issues) • [Star](https://github.com/AnonBOTpl/WinLog-Analyzer)

</div>
