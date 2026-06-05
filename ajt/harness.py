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


class GroqAttacker:
    """Live attacker. Not exercised by the offline test suite (needs a key)."""

    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY not set")

    def generate(self, prompt: str) -> str:
        import requests
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
