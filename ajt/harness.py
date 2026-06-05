import os
import time
from typing import Protocol


class Attacker(Protocol):
    def generate(self, prompt: str) -> str: ...


class MockAttacker:
    """Deterministic attacker for offline tests."""

    def __init__(self, response: str):
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


def _post(url: str, headers: dict, payload: dict, timeout: float = 90.0,
          retries: int = 5) -> dict:
    """POST with exponential backoff on 429 / 5xx (honours Retry-After)."""
    import requests
    delay = 2.0
    last = None
    for _ in range(retries):
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 429 or resp.status_code >= 500:
            ra = resp.headers.get("Retry-After", "")
            wait = float(ra) if ra.replace(".", "", 1).isdigit() else delay
            time.sleep(min(wait, 30.0))
            delay = min(delay * 2, 30.0)
            last = resp
            continue
        resp.raise_for_status()
        return resp.json()
    if last is not None:
        last.raise_for_status()
    raise RuntimeError("request failed after retries")


def _chat_completion(base_url: str, api_key: str, model: str, prompt: str,
                     temperature: float = 0.7) -> str:
    """OpenAI-compatible chat endpoint (Groq, OpenRouter, Together, Cerebras, Gemini)."""
    data = _post(
        base_url,
        {"Authorization": f"Bearer {api_key}"},
        {"model": model, "messages": [{"role": "user", "content": prompt}],
         "temperature": temperature},
    )
    return data["choices"][0]["message"]["content"]


# provider -> (base_url, env_var) for every OpenAI-compatible backend
OPENAI_COMPAT = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
    "together": ("https://api.together.xyz/v1/chat/completions", "TOGETHER_API_KEY"),
    "cerebras": ("https://api.cerebras.ai/v1/chat/completions", "CEREBRAS_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "GEMINI_API_KEY"),
}


class OpenAICompatAttacker:
    def __init__(self, base_url: str, model: str, api_key: str):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str) -> str:
        return _chat_completion(self.base_url, self.api_key, self.model, prompt)


class AnthropicAttacker:
    """Frontier reference point. Used to measure refusal, not to publish a
    jailbreak recipe."""
    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str, api_key: str | None = None, max_tokens: int = 1500):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

    def generate(self, prompt: str) -> str:
        data = _post(
            self.BASE_URL,
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01",
             "content-type": "application/json"},
            {"model": self.model, "max_tokens": self.max_tokens,
             "messages": [{"role": "user", "content": prompt}]},
        )
        return "".join(block.get("text", "") for block in data.get("content", []))


def make_attacker(provider: str, model_id: str) -> Attacker:
    if provider == "anthropic":
        return AnthropicAttacker(model=model_id)
    if provider in OPENAI_COMPAT:
        base_url, env_var = OPENAI_COMPAT[provider]
        api_key = os.environ.get(env_var)
        if not api_key:
            raise RuntimeError(f"{env_var} not set")
        return OpenAICompatAttacker(base_url, model_id, api_key)
    raise ValueError(f"unknown provider: {provider}")
