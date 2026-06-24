<div align="center">

# 🔍 WinLog Analyzer

**Analizator dzienników zdarzeń Windows z analizą AI**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.8%2B-41CD52?style=flat&logo=qt&logoColor=white)
![Platforma](https://img.shields.io/badge/Platforma-Windows-0078D4?style=flat&logo=windows&logoColor=white)
![Licencja](https://img.shields.io/badge/Licencja-MIT-yellow?style=flat)

[Funkcje](#funkcje) • [Instalacja](#instalacja) • [Konfiguracja](#konfiguracja) • [Użycie](#użycie) • [Testy](#testy) • [Struktura projektu](#struktura-projektu)

---

</div>

## 📋 Opis

**WinLog Analyzer** to aplikacja desktopowa dla systemu Windows, która odczytuje, filtruje i analizuje dzienniki zdarzeń Windows przy pomocy sztucznej inteligencji. Obsługuje **4 dostawców AI** (Google Gemini, Claude, OpenAI, Groq) i oferuje nowoczesny, ciemny interfejs zbudowany na PyQt6.

Aplikacja pomaga administratorom systemów i specjalistom IT szybko identyfikować problemy, dostarczając wyjaśnienia AI, oceny powagi oraz kroki naprawcze dla zdarzeń Windows.

## ✨ Funkcje

### 📊 Odczyt dzienników zdarzeń
- Odczytuje wszystkie **1193+ kanały dzienników zdarzeń Windows** (System, Aplikacja, Zabezpieczenia, Konfiguracja, PowerShell itp.)
- Inteligentne filtrowanie kanałów — pomija kanały Analityczne/Debug/Diagnostyczne/Wydajnościowe/Śledzenia
- Konwersja strefy czasowej do Europy/Warszawy
- Ładowanie w tle — brak zamrażania interfejsu podczas uruchamiania
- 10-sekundowy timeout na renderowanie XML — zapobiega zawieszaniu na problematycznych zdarzeniach
- **Wyszukiwanie zdarzeń** w czasie rzeczywistym po wszystkich kolumnach lub filtrowanie po Źródle, Event ID lub Opisie

### 🔬 Analiza AI
- **4 dostawców**: Google Gemini, Claude (Anthropic), OpenAI, Groq
- Analiza pojedynczego zdarzenia lub **analiza zbiorcza** (z paskiem postępu i przyciskiem anulowania)
- Strukturyzowane odpowiedzi z markerami emoji:
  - 🔍 Co to jest
  - ⚠️ Czy to poważne
  - 🔧 Co zrobić
  - 💡 Wskazówka
- Auto-zapis historii analiz do bazy SQLite

### 🎛️ Filtrowanie i nawigacja
- Filtr poziomu: Błędy i Ostrzeżenia / Tylko błędy / Tylko ostrzeżenia
- Filtr czasu: Ostatnie 24h / 7d / 30d / Wszystko / Własny zakres dat
- Drzewo nawigacji: Wszystkie, Krytyczne, Dzienniki systemowe, Aplikacje i usługi
- Wyszukiwanie w czasie rzeczywistym z wyborem kolumny
- Wielokrotny wybór z trwałymi checkboxami

### 📈 Porównanie i historia
- **Historia analiz** — przeglądaj wszystkie poprzednie analizy ze szczegółowym widokiem
- **Tryb porównania** — porównaj bieżące zdarzenia z historią (Nowe / Rozwiązane / Powtórzone)
- Kodowanie kolorami: zielony (nowe), szary (rozwiązane), żółty (powtórzone)

### 📤 Eksport
- Eksport raportów do **HTML** (ciemny motyw) lub **TXT**
- Eksport zbiorczy po analizie wielu zdarzeń

### 🌐 Internacjonalizacja
- Dołączone tłumaczenia angielskie i polskie
- Łatwe dodawanie nowych języków (patrz `locales/CONTRIBUTING.md`)
- Odpowiedzi AI dopasowują się do wybranego języka

### 🎨 Ciemny motyw
- Nowoczesny ciemny interfejs (#1A1A2E, #16213E, #ECF0F1)
- Niestandardowy arkusz stylów QSS dla wszystkich widżetów
- Kodowanie kolorami poziomów zdarzeń: Błąd (czerwony), Ostrzeżenie (pomarańczowy)

## 🚀 Instalacja

### Wymagania wstępne
- **Windows** (wymagany do API dzienników zdarzeń Windows)
- **Python 3.10 lub nowszy**
- **UV** (szybki menedżer pakietów Python)

### Szybka instalacja

```powershell
# Sklonuj repozytorium
git clone https://github.com/AnonBOTpl/WinLog-Analyzer.git
cd WinLog-Analyzer

# Uruchom instalator
install.bat
```

Lub ręcznie:

```powershell
uv venv
uv sync
```

### Uruchamianie

```powershell
start.bat
```

Lub bezpośrednio:

```powershell
uv run python main.py
```

## ⚙️ Konfiguracja

### Konfiguracja dostawcy AI

1. Otwórz **Ustawienia** z paska narzędzi
2. Wybierz dostawcę AI:
   - **Google Gemini** — Uzyskaj darmowy klucz API na [Google AI Studio](https://aistudio.google.com/)
   - **Claude (Anthropic)** — Uzyskaj klucz API na [console.anthropic.com](https://console.anthropic.com/)
   - **OpenAI** — Uzyskaj klucz API na [platform.openai.com](https://platform.openai.com/)
   - **Groq** — Uzyskaj darmowy klucz API na [console.groq.com](https://console.groq.com/)
3. Wprowadź klucz API i kliknij **Zapisz klucz** (przechowywany bezpiecznie w Menedżerze poświadczeń Windows)
4. Kliknij **Testuj klucz**, aby zweryfikować
5. Kliknij **Skanuj modele**, aby pobrać dostępne modele
6. Wybierz model i kliknij **OK**

### Język

Zmień język w **Ustawienia → Język**. Aplikacja uruchomi się ponownie automatycznie.

## 🎮 Użycie

### Podstawowy przepływ pracy

1. Uruchom aplikację — zdarzenia ładują się automatycznie
2. Użyj **drzewa nawigacji** po lewej stronie, aby filtrować według źródła
3. Użyj filtrów **poziomu** i **czasu** na pasku narzędzi
4. **Wyszukaj** konkretny tekst za pomocą paska wyszukiwania nad tabelą
5. Kliknij zdarzenie, aby wyświetlić szczegóły w panelu AI
6. Kliknij **Analizuj**, aby uzyskać analizę AI
7. Dla wielu zdarzeń **zaznacz checkboxy** i kliknij **Analizuj**

### Wyszukiwanie

Pasek wyszukiwania obsługuje filtrowanie w czasie rzeczywistym bez rozróżniania wielkości liter:

- **Wszystkie kolumny** — przeszukuje Źródło, Event ID, Poziom i Opis
- **Źródło** — filtruj według źródła zdarzenia
- **Event ID** — filtruj według numeru ID zdarzenia
- **Opis** — filtruj według treści komunikatu zdarzenia

### Analiza zbiorcza

1. Zaznacz checkboxy przy zdarzeniach do analizy
2. Kliknij **Analizuj** — pasek postępu pokazuje status
3. Kliknij poszczególne wyniki na liście, aby wyświetlić szczegóły
4. Kliknij **Eksportuj raport**, aby zapisać jako HTML lub TXT

### Porównanie

1. Najpierw wykonaj kilka analiz AI (wymagana historia)
2. Kliknij **Porównaj** na pasku narzędzi
3. Wyświetl zakładki: **Nowe** zdarzenia, **Rozwiązane** zdarzenia, **Wszystkie** zdarzenia

## 🧪 Testy

Uruchom zestaw testów:

```powershell
test.bat
```

Lub ręcznie:

```powershell
uv run python -m unittest discover tests/ -v
```

Obecne pokrycie testami: **39 testów** obejmujących:
- `core/log_reader.py` — parsowanie XML, konwersja czasu, stałe
- `providers/base.py` — system prompt, budowanie promptu, parsowanie sekcji

## 📁 Struktura projektu

```
WinLog Analyzer/
├── main.py                  # Punkt wejścia
├── pyproject.toml           # Zależności i metadane
├── install.bat              # Instalator jednym kliknięciem
├── start.bat                # Uruchamianie aplikacji
├── test.bat                 # Uruchamianie testów
├── .python-version          # Wersja Pythona dla uv
│
├── core/                    # Logika biznesowa
│   ├── log_reader.py        # Czytnik dzienników Windows (API win32evtlog)
│   ├── log_filter.py        # Filtrowanie zdarzeń (poziom, data, źródło)
│   ├── analysis_worker.py   # Workery QThread działające w tle
│   ├── ai_client.py         # Agregator dostawców AI
│   ├── exporter.py          # Eksport raportów (TXT/HTML)
│   ├── history.py           # Historia analiz SQLite
│   ├── comparator.py        # Silnik porównywania zdarzeń
│   ├── i18n.py              # Internacjonalizacja
│   └── paths.py             # Rozwiązywanie ścieżek plików
│
├── providers/               # Integracje dostawców AI
│   ├── base.py              # Abstrakcyjna klasa AIProvider
│   ├── gemini.py            # Google Gemini
│   ├── anthropic.py         # Claude (Anthropic)
│   ├── openai.py            # OpenAI
│   └── groq.py              # Groq
│
├── ui/                      # Interfejs użytkownika PyQt6
│   ├── main_window.py       # Główne okno (pasek narzędzi, spliter, pasek statusu)
│   ├── log_table.py         # Tabela dzienników z checkboxami
│   ├── ai_panel.py          # Panel analizy AI
│   ├── settings_dialog.py   # Okno ustawień
│   ├── history_dialog.py    # Historia analiz
│   ├── compare_panel.py     # Porównanie zdarzeń
│   └── styles.qss           # Arkusz stylów ciemnego motywu
│
├── locales/                 # Pliki tłumaczeń
│   ├── en.json              # Angielski
│   ├── pl.json              # Polski
│   └── CONTRIBUTING.md      # Instrukcja dodawania języków
│
├── tests/                   # Testy jednostkowe
│   ├── test_base.py         # Testy dla providers/base.py
│   └── test_log_reader.py   # Testy dla core/log_reader.py
│
└── scripts/
    └── png2ico.py           # Narzędzie konwersji PNG → ICO
```

## 🛠️ Stack technologiczny

| Komponent | Technologia |
|-----------|-------------|
| **Język** | Python 3.10+ |
| **Framework UI** | PyQt6 |
| **API dzienników** | pywin32 (win32evtlog) |
| **Dostawcy AI** | Google Gemini, Claude, OpenAI, Groq |
| **Baza danych** | SQLite (przez moduł historii) |
| **Przechowywanie kluczy** | Menedżer poświadczeń Windows (keyring) |
| **HTTP** | requests |
| **Strefa czasowa** | tzdata |
| **Menedżer pakietów** | uv |

## 🤝 Współpraca

Zapraszamy do współpracy! Oto jak możesz pomóc:

1. **Dodaj nowy język** — zobacz `locales/CONTRIBUTING.md`
2. **Dodaj nowego dostawcę AI** — zaimplementuj `AIProvider` z `providers/base.py`
3. **Napisz testy** — popraw pokrycie w `tests/`
4. **Zgłoś błędy** — otwórz zgłoszenie na GitHub
5. **Zasugeruj funkcje** — otwórz dyskusję

## 📄 Licencja

Ten projekt jest open source. Szczegóły w pliku LICENSE.

---

<div align="center">

**Stworzone z ❤️ przez [AnonBOTpl](https://github.com/AnonBOTpl)**

[Zgłoś błąd](https://github.com/AnonBOTpl/WinLog-Analyzer/issues) • [Zaproponuj funkcję](https://github.com/AnonBOTpl/WinLog-Analyzer/issues) • [Oznacz gwiazdką](https://github.com/AnonBOTpl/WinLog-Analyzer)

</div>
