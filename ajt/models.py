from dataclasses import dataclass


@dataclass
class ModelSpec:
    label: str
    provider: str   # "groq" | "openrouter"
    model_id: str
    family: str


# A diverse probe set spanning families, sizes, and safety-tuning levels.
# Invalid/unavailable model ids are skipped gracefully by the probe.
PROBE_MODELS = [
    ModelSpec("llama-3.3-70b", "groq", "llama-3.3-70b-versatile", "llama"),
    ModelSpec("llama-3.1-8b", "groq", "llama-3.1-8b-instant", "llama"),
    ModelSpec("gemma2-9b", "groq", "gemma2-9b-it", "gemma"),
    ModelSpec("qwen-2.5-coder-32b", "openrouter", "qwen/qwen-2.5-coder-32b-instruct", "qwen"),
    ModelSpec("mistral-small-24b", "openrouter", "mistralai/mistral-small-24b-instruct-2501", "mistral"),
    ModelSpec("deepseek-chat", "openrouter", "deepseek/deepseek-chat", "deepseek"),
]
