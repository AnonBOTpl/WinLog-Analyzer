import json
import requests
from providers.base import AIProvider, system_prompt
from core.i18n import t

API_BASE = "https://api.anthropic.com/v1"
DEFAULT_MODEL = "claude-haiku-4-5"


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) provider using the Messages API.

    Default model: claude-haiku-4-5.
    """

    def __init__(self, api_key: str = "", model: str = DEFAULT_MODEL):
        super().__init__(api_key, model)

    def analyze(self, event: dict) -> dict:
        if not self.api_key:
            return {"error": t("error_api_no_key")}

        prompt = self._build_prompt(event)
        url = f"{API_BASE}/messages"

        try:
            resp = requests.post(
                url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": system_prompt(),
                    "messages": [{"role": "user", "content": prompt}],
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
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
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
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return sorted(m.get("id", "") for m in data.get("data", []))
        except requests.RequestException:
            return []

    def _parse_response(self, data: dict) -> dict:
        try:
            content_blocks = data.get("content", [])
            text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    break
            if not text:
                return {"error": t("error_no_response")}
            return self._parse_sections(text)
        except (KeyError, IndexError, TypeError) as e:
            return {"error": t("error_parse", msg=str(e))}
