from abc import ABC, abstractmethod
from core.i18n import t


def system_prompt() -> str:
    """Build localized system prompt using current language."""
    lang_name = t("_language_name").lower()
    return (
        f"Jesteś ekspertem Windows. Odpowiadaj TYLKO w języku: {lang_name}.\n"
        f"Format odpowiedzi:\n"
        f"🔍 {t('section_what_is')}: ...\n"
        f"⚠️ {t('section_is_serious')}: ...\n"
        f"🔧 {t('section_what_to_do')}: ...\n"
        f"💡 {t('section_tip')}: ..."
    )


class AIProvider(ABC):
    """Abstract base class for AI provider integrations.

    Subclasses must implement analyze() and validate_api_key().
    The _build_prompt and _parse_sections helpers format input and
    extract structured fields (explanation, severity, steps, tip)
    from AI responses using emoji-based section markers.
    """

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def analyze(self, event: dict) -> dict:
        """Send an event to the AI and return a structured analysis.

        Returns a dict with keys: explanation, severity, steps, tip
        or {"error": "..."} on failure.
        """
        ...

    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        """Check whether the given API key is valid."""
        ...

    def list_models(self, api_key: str) -> list[str]:
        """Fetch available models (override if the provider supports listing)."""
        return []

    def _build_prompt(self, event: dict) -> str:
        event_lines = [
            f"{t('field_source')}: {event.get('SourceName', '?')}",
            f"{t('field_event_id')}: {event.get('EventID', '?')}",
            f"{t('field_level')}: {event.get('Level', '?')}",
            f"{t('field_datetime')}: {event.get('TimeGenerated', '?')}",
            f"{t('section_event_description')}: {event.get('Message', '?')}",
        ]
        return "\n".join(event_lines)

    @staticmethod
    def _parse_sections(text: str) -> dict:
        """Parse an AI response into structured sections by emoji markers.

        Recognizes: 🔍 (explanation), ⚠️ (severity), 🔧 (steps), 💡 (tip).
        """
        result = {"explanation": "", "severity": "", "steps": "", "tip": ""}
        emoji_map = {
            "🔍": "explanation",
            "⚠️": "severity",
            "🔧": "steps",
            "💡": "tip",
        }
        current_section = None
        current_text = []
        for line in text.split("\n"):
            line_stripped = line.strip()
            found = False
            for emoji, key in emoji_map.items():
                if line_stripped.startswith(emoji):
                    if current_section and current_text:
                        result[current_section] = "\n".join(current_text).strip()
                    current_section = key
                    current_text = []
                    rest = line_stripped[len(emoji):].strip()
                    colon_idx = rest.find(":")
                    if colon_idx >= 0:
                        rest = rest[colon_idx + 1:].strip()
                    if rest in ("...",):
                        rest = ""
                    if rest:
                        current_text.append(rest)
                    found = True
                    break
            if not found and current_section:
                current_text.append(line_stripped)
        if current_section and current_text:
            result[current_section] = "\n".join(current_text).strip()
        return result
