# Adding a new language to WinLog Analyzer

1. Copy `en.json` and rename it to your language code (e.g. `de.json` for German)
2. Edit `_language_name` to the language name in that language (e.g. `"Deutsch"`)
3. Edit `_language_code` to match the filename (e.g. `"de"`)
4. Translate all values - do NOT change the keys
5. Leave technical strings unchanged: provider names, error codes, format placeholders like `{provider}`, `{count}`
6. The `section_*` keys control both the UI display AND the AI's system prompt (section headers used in responses) — translate them naturally
7. Submit a Pull Request on GitHub

The app will automatically detect your file on next launch.
