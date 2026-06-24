# Changelog

## v2.2.0 (2026-06-24)

### Jakość kodu i refaktoring
- Usunięto wbudowane tłumaczenia (`_ENGLISH`, `_POLISH`, `_EMBEDDED`) z `core/i18n.py` — tłumaczenia wyłącznie z plików JSON
- Wyodrębniono wspólne helpery tabel (`_create_table`, `_event_data`, `_set_row`) w `compare_panel.py` — eliminacja duplikacji kodu
- Usunięto nieużywany parametr `label` z `_make_table()` i jej wywołań
- Zastąpiono `os.spawnl` przez `subprocess.Popen` w `_restart_app()` dla lepszej przenośności
- Dodano pełne docstringi do wszystkich publicznych funkcji w `core/` i `providers/` (14 plików)

### Stabilność i bezpieczeństwo
- Dodano **timeout QTimer** dla wszystkich workerów działających w tle:
  - LoadEventsWorker: 60s
  - AnalysisWorker: 120s
  - BatchAnalysisWorker: 120s na zdarzenie
  - TestKeyWorker: 15s
  - ScanModelsWorker: 30s
- Dodano guard przed wielokrotnym uruchamianiem `LoadEventsWorker` przy szybkim klikaniu Refresh
- Dodano guard przed nadpisywaniem `self._worker` w `_test_key()` i `_scan_models()`
- Dodano **indeksy SQLite** (`idx_analyses_analyzed_at`, `idx_analyses_source_event`) dla wydajności historii
- Dodano **300s TTL** dla `_QUERYABLE_CACHE` — cache wygasa i ponownie sprawdza kanały
- Dodano **10s timeout** dla `_evt_render_xml` przez `ThreadPoolExecutor` — zapobiega zawieszaniu na problematycznych eventach
- Dodano `atexit` cleanup dla puli wątków renderowania

### Zależności i kompatybilność
- Obniżono `requires-python` z `>=3.12` do `>=3.10` (wszystkie biblioteki wspierają 3.10)
- Usunięto nieużywany `import win32evtlogutil` i stałą `BATCH_SIZE_BYTES` z `core/log_reader.py`
- Usunięto martwy kod `get_events()` (stary fallback ReadEventLog API)
- Usunięto zduplikowaną metodę `_on_export()` z `ui/main_window.py`

### Testy
- Dodano katalog `tests/` z zestawem testów jednostkowych
- `tests/test_base.py` — 15 testów dla `system_prompt()`, `_build_prompt()`, `_parse_sections()`
- `tests/test_log_reader.py` — 24 testy dla `_parse_iso_time()`, `_parse_event_xml()`, stałych
- Dodano `test.bat` — uruchamianie testów jednym kliknięciem z pełnym wynikiem
- Wszystkie **39 testów przechodzi**

### Dokumentacja
- Kompletny przepis README: funkcje, instalacja, konfiguracja, użycie, testowanie, struktura projektu
- Dodano link GitHub: `https://github.com/AnonBOTpl/WinLog-Analyzer`
- Zaktualizowano `.gitignore` — dodano wzorce `test.bat` i `tests/__pycache__/`

---

## v2.1.1 (2026-06-24)

### Zmiany
- Porzucono pakowanie PyInstaller / Nuitka – aplikacja uruchamiana przez `uv run python main.py`
- `start.bat` – uruchamia bezpośrednio przez `uv`, bez sprawdzania .exe
- `install.bat` – uproszczony do `uv venv` + `uv sync`, bez budowania
- Domyślny język zmieniony z polskiego na angielski
- Tłumaczenia EN i PL wbudowane w `core/i18n.py` – brak zależności od zewnętrznych plików JSON
- `available_languages()` sprawdza `sys._MEIPASS` dla locales w frozen; wbudowane słowniki zawsze dostępne
- `_restart_app()` naprawiony dla frozen/dev; używa `os._exit(0)` by uniknąć warninga PyInstaller o temp dir
- Nowy przycisk "Usuń klucz" w Ustawieniach (`keyring.delete_password`)

### Naprawy błędów
- `core/i18n.py` – dodano brakujący `import sys` / `from pathlib import Path` powodujący `NameError`
- `core/paths.py` – przywrócono `_base_path()` do `sys.executable.parent`, usunięto przerost `_candidates()`
- Obsługa braku plików locale (loguje warning, używa wbudowanych tłumaczeń)

---

## v2.1.0 (2026-06-24)

### Nowe funkcje
- Internacjonalizacja (i18n) – przełączanie języka PL/EN w Ustawieniach
- `core/i18n.py` – moduł tłumaczeń z `load()`, `t()`, `available_languages()`
- `locales/en.json`, `locales/pl.json` – 113 kluczy tłumaczeń każdy
- System prompt AI (`providers/base.py`) dostosowuje się do języka (sekcje odpowiedzi, etykiety pól)
- Wszystkie komunikaty błędów w providerach (4 × Gemini/Claude/OpenAI/Groq) przez `t()`
- ComboBox języka w Ustawieniach + automatyczny restart przy zmianie
- `locales/CONTRIBUTING.md` – instrukcja dodawania nowego języka

### Usprawnienia
- Checkbox multi-select zamiast Top N – zaznaczenie trwałe między filtrami, sygnatura `(Source, EventID, TimeGenerated)`
- Przycisk "Odznacz wszystkie" w panelu AI
- Kopiowalne odpowiedzi AI (QLabel → QTextEdit readOnly)
- Renderowanie Markdown w odpowiedziach AI: `**bold**`, `*italic*`, listy `-`/`*`
- Ładowanie zdarzeń w tle (`LoadEventsWorker` w `QThread`) – UI nie zamarza przy starcie
- Timeout API: 30s → 60s we wszystkich 4 providerach
- Przyjazny komunikat błędu 503 (przeciążenie API, sugestia odczekania)
- Nazwy źródeł Windows (Application → Aplikacja itp.) przez `t()` w obu językach
- QSS dla QLineEdit, QProgressBar, QListWidget, QScrollBar, QSpinBox
- Optymalizacja tabeli: `setUpdatesEnabled(False)` + `blockSignals(True)` podczas przebudowy

### Naprawy błędów
- Level mapping: Evt Level=2 → "Error", Level=3 → "Warning" (Evt API)
- `_compute_source_counts()` używa stałej `EVT_ERROR` zamiast magicznej wartości
- BUG-01: Usunięto zduplikowaną `get_all_sources()` w `core/log_reader.py`
- BUG-02: `_load_events()` przeniesiony do `LoadEventsWorker(QThread)` – UI nie blokuje się
- BUG-04: `ScanModelsWorker` – dodano `self._worker = None` w `_on_scan_finished`
- BUG-05: Filtr "Krytyczne" pokazuje teraz Error(2)+Critical(1) zamiast tylko Critical(1)
- BUG-06: `comparator.py` używa publicznej `get_connection()` zamiast `_get_conn`
- BUG-07: Zmiana providera w ustawieniach resetuje listę modeli
- Sygnał `pyqtSignal(dict)` → `pyqtSignal(object)` – brak crasha przy `emit(None)`

---

## v2.0.0 (2026-06-24)

### Nowi providerzy AI
- `providers/base.py` – klasa abstrakcyjna `AIProvider` z `_build_prompt()`, `_parse_sections()`
- `providers/anthropic.py` – Claude API (claude-haiku-4-5)
- `providers/openai.py` – OpenAI (gpt-4o-mini)
- `providers/groq.py` – Groq (llama-3.1-8b-instant)
- `providers/gemini.py` – refaktor do dziedziczenia z `AIProvider`
- `core/ai_client.py` – agregacja providerów: `get_provider()`, `analyze_event()`, `validate_key()`, `list_models()`
- Wspólny system prompt, timeout 60s, obsługa 503

### Analiza zbiorcza
- `BatchAnalysisWorker(QThread)` – sekwencyjne zapytania, 1s pauza między requestami
- Progress bar w panelu AI (`x / N przeanalizowano`)
- Przycisk "Przerwij" – anulowanie analizy
- Lista wyników (QListWidget) – kliknięcie pokazuje szczegóły
- Błąd pojedynczego zdarzenia nie przerywa całej analizy

### Eksport raportu
- `core/exporter.py` – `export_txt()` i `export_html()`
- HTML z dark theme (#1A1A2E, #ECF0F1)
- Przycisk "Eksportuj" w panelu AI po zakończeniu analizy zbiorczej

### Historia analiz
- `core/history.py` – SQLite baza `data/winlog_history.db`
- Funkcje: `save_analysis()`, `get_history()`, `clear_history()`
- `ui/history_dialog.py` – tabela z kolumnami Data/Źródło/Event ID/Poziom/Provider
- Szczegóły analizy w read-only QTextEdit po kliknięciu wiersza
- Auto-zapis po każdej analizie (pojedynczej i zbiorczej)

### Wyszukiwanie i filtrowanie
- QLineEdit "Szukaj..." nad tabelą (real-time, case-insensitive)
- ComboBox filtru kolumny: Wszystkie / Źródło / Event ID / Opis
- Statusbar: "X / Y zdarzeń"

### Porównanie analiz
- `core/comparator.py` – porównanie bieżących zdarzeń z historią SQLite
- `ui/compare_panel.py` – zakładki: Nowe / Rozwiązane / Wszystkie
- Kolorowanie: zielony (nowe), szary (rozwiązane), żółty (powtórzone)

### GitHub Releases
- `scripts/release.ps1` – build → zip → gh release upload
- `scripts/CHANGELOG.md` – dokumentacja zmian

### Pakowanie PyInstaller
- `winlog_analyzer.spec` – one-folder, windowed, hidden imports dla pywin32/keyring
- `install.bat` – instalacja od zera (bez UV, bez venv)
- `start.bat` – uruchamia .exe lub fallback do `uv run python main.py`
- `build.bat` – szybki rebuild
- `scripts/png2ico.py` – konwersja PNG → ICO
- `pyproject.toml` v2.0.0, optional-dependencies build z pyinstaller>=6

### Ikona i ścieżki
- `app.setWindowIcon(QIcon("ikona.png"))` – ikona w titlebar i taskbar
- `core/paths.py` – `resource_path()` dla plików w bundle, `data_file()` dla `%APPDATA%`
- Obsługa trybu frozen (PyInstaller) i dev (uv run)

---

## v1.0.0 (2026-06-23)

### Projekt i struktura
- Inicjalizacja projektu z UV, Python 3.12
- Struktura katalogów: `core/`, `ui/`, `providers/`, `config/`
- `pyproject.toml` – zależności: PyQt6, pywin32, requests, keyring, tzdata
- `main.py` – entry point z Fusion style i ciemnym motywem
- `.gitignore` – venv, `__pycache__`, dist/, build/

### Odczyt logów Windows
- `core/log_reader.py` – API `win32evtlog` (EvtQuery), 1193 kanałów
- `get_all_sources()` – dynamiczne skanowanie kanałów przez `EvtOpenChannelEnum`
- `get_events_from_sources()` – agregacja zdarzeń ze wszystkich kanałów
- Filtrowanie kanałów: pomijanie Analytic/Debug/Diagnostic/Performance/Trace
- Konwersja czasu UTC → Europe/Warsaw przez `zoneinfo`
- `_parse_event_xml()` – ekstrakcja SourceName, EventID, Level, Message, TimeGenerated

### Filtrowanie zdarzeń
- `core/log_filter.py` – filtrowanie po EventType (Error/Warning), dacie, źródle
- `filter_events()` – poziom + zakres czasowy + źródło

### Interfejs użytkownika
- `ui/main_window.py` – QMainWindow z toolbar, splitter (tabela 60% / panel AI 40%), statusbar
- `ui/log_table.py` – QTableWidget z kolumnami Data/Czas, Poziom, Źródło, Event ID, Opis
- Kolorowanie: Error (#E74C3C), Warning (#F39C12), tło (#16213E)
- `ui/ai_panel.py` – panel szczegółów zdarzenia z polami Źródło, Event ID, Poziom, Data, Opis
- Drzewo nawigacyjne (NavTree) – Wszystkie, Krytyczne, Dzienniki systemowe, Aplikacje i usługi
- Sortowanie po kolumnach, zaznaczenie wiersza

### Integracja Google Gemini
- `providers/gemini.py` – `GeminiProvider.analyze()`, `validate_api_key()`, `list_models()`
- Model domyślny: gemini-2.5-flash
- System prompt: ekspert Windows, odpowiedzi po polsku
- Struktura odpowiedzi: 🔍 Co to jest / ⚠️ Czy to poważne / 🔧 Co zrobić / 💡 Wskazówka
- `AnalysisWorker(QThread)` – zapytania AI w tle bez blokowania UI
- `BatchAnalysisWorker` – przygotowanie szkieletu

### Ustawienia
- `ui/settings_dialog.py` – wybór providera, klucz API (keyring, Windows Credential Manager)
- Skanowanie modeli z API, testowanie klucza
- ComboBox modeli, zapis do `config/settings.json`

### Ciemny motyw
- `ui/styles.qss` – dark theme: #1A1A2E, #16213E, #ECF0F1
- Font: Segoe UI, 10pt
- Stylowanie tabeli, przycisków, pól tekstowych

### Filtr czasowy
- ComboBox w toolbarze: 24h / 7d / 30d / Wszystko / Własny zakres
- QDateEdit dla własnego zakresu dat
- Filtrowanie in-memory na już pobranych danych
