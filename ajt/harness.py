import os
from typing import Protocol


class Attacker(Protocol):
    def generate(self, prompt: str) -> str: ...


class MockAttacker:
    """Deterministic attacker for offline tests."""

    def __init__(self, response: str):
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


def _chat(base_url: str, api_key: str, model: str, prompt: str,
          temperature: float = 0.7, timeout: float = 90.0) -> str:
    """One-shot completion against any OpenAI-compatible chat endpoint."""
    import requests
    resp = requests.post(
        base_url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


class GroqAttacker:
    """Live attacker via Groq (free tier). Not exercised by the offline suite."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set")

    def generate(self, prompt: str) -> str:
        return _chat(self.BASE_URL, self.api_key, self.model, prompt)


class OpenRouterAttacker:
    """Live attacker via OpenRouter (broad open-weight catalogue)."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str, api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")

    def generate(self, prompt: str) -> str:
        return _chat(self.BASE_URL, self.api_key, self.model, prompt)


def make_attacker(provider: str, model_id: str) -> Attacker:
    if provider == "groq":
        return GroqAttacker(model=model_id)
    if provider == "openrouter":
        return OpenRouterAttacker(model=model_id)
    raise ValueError(f"unknown provider: {provider}")
