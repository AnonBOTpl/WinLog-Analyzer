from providers.gemini import GeminiProvider
from providers.anthropic import AnthropicProvider
from providers.openai import OpenAIProvider
from providers.groq import GroqProvider
from providers.base import AIProvider

PROVIDERS: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "claude": AnthropicProvider,
    "openai": OpenAIProvider,
    "groq": GroqProvider,
}


def get_provider(provider_name: str, api_key: str = "", model: str = "") -> AIProvider:
    """Get an AI provider instance by name.

    Args:
        provider_name: One of "gemini", "claude", "openai", "groq".
        api_key: API key for the provider.
        model: Model name to use.

    Returns:
        Initialized AIProvider subclass instance.

    Raises:
        ValueError: If provider_name is unknown.
    """
    cls = PROVIDERS.get(provider_name)
    if cls is None:
        raise ValueError(f"Nieznany provider: {provider_name}")
    return cls(api_key=api_key, model=model)


def analyze_event(provider_name: str, api_key: str, model: str, event: dict) -> dict:
    """Analyze a single Windows event using the specified AI provider.

    Returns a dict with keys: explanation, severity, steps, tip
    or {"error": "..."} on failure.
    """
    provider = get_provider(provider_name, api_key, model)
    return provider.analyze(event)


def validate_key(provider_name: str, api_key: str) -> bool:
    """Check whether an API key is valid for the given provider."""
    provider = get_provider(provider_name)
    return provider.validate_api_key(api_key)


def list_models(provider_name: str, api_key: str) -> list[str]:
    """Fetch available model names from the provider's API."""
    provider = get_provider(provider_name)
    return provider.list_models(api_key)
