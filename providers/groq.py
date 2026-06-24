import json
import requests
from providers.base import AIProvider, system_prompt
from core.i18n import t

API_BASE = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.1-8b-instant"


class GroqProvider(AIProvider):
    """Groq provider (OpenAI-compatible API).

    Default model: llama-3.1-8b-instant.
    """

    def __init__(self, api_key: str = "", model: str = DEFAULT_MODEL):
        super().__init__(api_key, model)

    def analyze(self, event: dict) -> dict:
        if not self.api_key:
            return {"error": t("error_api_no_key")}

        prompt = self._build_prompt(event)
        url = f"{API_BASE}/chat/completions"

        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt()},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 1024,
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.Timeout:
            return {"error": t("error_timeout", timeout=60)}
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            if status == 503:
                return {"error": t("error_503")}
            return {"error": t("error_api_http", status=status, msg=str(e))}
        except requests.RequestException as e:
            return {"error": t("error_network", msg=str(e))}

        return self._parse_response(data)

    def validate_api_key(self, api_key: str) -> bool:
        if not api_key:
            return False
        try:
            resp = requests.get(
                f"{API_BASE}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self, api_key: str) -> list[str]:
        if not api_key:
            return []
        try:
            resp = requests.get(
                f"{API_BASE}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return sorted(m.get("id", "") for m in data.get("data", []))
        except requests.RequestException:
            return []

    def _parse_response(self, data: dict) -> dict:
        try:
            choices = data.get("choices", [])
            if not choices:
                return {"error": t("error_no_response")}
            text = choices[0].get("message", {}).get("content", "")
            if not text:
                return {"error": t("error_no_response")}
            return self._parse_sections(text)
        except (KeyError, IndexError, TypeError) as e:
            return {"error": t("error_parse", msg=str(e))}
