import json
import logging
import sys
from pathlib import Path
from core.paths import resource_path


_translations: dict[str, str] = {}
_fallback: dict[str, str] = {}
_current_lang: str = "en"


def _find_locales_dir() -> Path:
    locales = resource_path("locales")
    if locales.is_dir():
        return locales
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            alt = Path(meipass) / "locales"
            if alt.is_dir():
                return alt
    return locales


def _locale_path(language_code: str) -> Path:
    locales_dir = _find_locales_dir()
    return locales_dir / f"{language_code}.json"


def _load_json(language_code: str) -> dict[str, str]:
    path = _locale_path(language_code)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load(language_code: str) -> None:
    """Load translations for the given language code.

    Reads from locales/<code>.json. Falls back to en.json for missing keys.
    If the file is missing, translations will be empty (t() returns the key).
    """
    global _translations, _current_lang, _fallback
    _current_lang = language_code

    _fallback = _load_json("en")

    if language_code == "en":
        _translations = dict(_fallback)
        return

    lang_data = _load_json(language_code)
    if lang_data:
        _translations = dict(_fallback)
        _translations.update(lang_data)
    else:
        _translations = dict(_fallback)


def t(key: str, default: str | None = None, **kwargs) -> str:
    """Get a translated string by key.

    Args:
        key: Translation key.
        default: Fallback string if key is missing (defaults to returning the key itself).
        **kwargs: Format arguments interpolated into the translation.

    Returns:
        The translated string, or the key if not found, or default if provided.
    """
    value = _translations.get(key)
    if value is None:
        if default is not None:
            return default
        logging.warning("Missing translation key: %s", key)
        return key
    if kwargs:
        return value.format(**kwargs)
    return value


def available_languages() -> list[dict]:
    """Scan locales/ directory and return available languages.

    Each entry: {"code": "pl", "name": "Polski"}
    """
    result = []
    locales_dir = _find_locales_dir()
    if locales_dir.is_dir():
        for fp in sorted(locales_dir.glob("*.json")):
            try:
                with open(fp, encoding="utf-8") as f:
                    data = json.load(f)
                result.append({
                    "code": data.get("_language_code", fp.stem),
                    "name": data.get("_language_name", fp.stem),
                })
            except Exception:
                logging.warning("Failed to read locale file: %s", fp.name)
    return result
