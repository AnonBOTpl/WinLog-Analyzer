import requests
from providers.base import AIProvider, system_prompt
from core.i18n import t

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiProvider(AIProvider):
    """Google Gemini provider using the generateContent API.

    Default model: gemini-2.5-flash.
    Filters models by supportedGenerationMethods.
    """

    def __init__(self, api_key: str = "", model: str = DEFAULT_MODEL):
        super().__init__(api_key, model)

    def analyze(self, event: dict) -> dict:
        if not self.api_key:
            return {"error": t("error_api_no_key")}

        prompt = self._build_prompt(event)
        url = f"{API_BASE}/models/{self.model}:generateContent"

        try:
            resp = requests.post(
                url,
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": system_prompt()}]},
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
        url = f"{API_BASE}/models"
        try:
            resp = requests.get(url, params={"key": api_key}, timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self, api_key: str) -> list[str]:
        if not api_key:
            return []
        url = f"{API_BASE}/models"
        try:
            resp = requests.get(url, params={"key": api_key}, timeout=15)
            resp.raise_for_status()
            models = resp.json().get("models", [])
            result = []
            for m in models:
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    name = m.get("name", "")
                    if name.startswith("models/"):
                        name = name[7:]
                    result.append(name)
            return sorted(result)
        except requests.RequestException:
            return []

    def _parse_response(self, data: dict) -> dict:
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return {"error": t("error_no_response")}

            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text:
                return {"error": t("error_no_response")}

            return self._parse_sections(text)
        except (KeyError, IndexError, TypeError) as e:
            return {"error": t("error_parse", msg=str(e))}
