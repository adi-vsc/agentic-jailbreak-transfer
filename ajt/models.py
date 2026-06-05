from dataclasses import dataclass


@dataclass
class ModelSpec:
    label: str
    provider: str   # "groq" | "openrouter" | "anthropic"
    model_id: str
    family: str
    note: str = ""


# Diverse probe set: families, sizes, safety-tuning levels, and a frontier
# reference. Unavailable ids are skipped gracefully by the probe.
PROBE_MODELS = [
    # --- Groq (free tier, OpenAI-compatible) ---
    ModelSpec("llama-3.3-70b", "groq", "llama-3.3-70b-versatile", "llama"),
    ModelSpec("llama-3.1-8b", "groq", "llama-3.1-8b-instant", "llama", "small"),
    ModelSpec("llama-4-scout-17b", "groq", "meta-llama/llama-4-scout-17b-16e-instruct", "llama4"),
    ModelSpec("gpt-oss-20b", "groq", "openai/gpt-oss-20b", "gpt-oss"),
    ModelSpec("gpt-oss-120b", "groq", "openai/gpt-oss-120b", "gpt-oss", "large"),
    ModelSpec("gpt-oss-safeguard-20b", "groq", "openai/gpt-oss-safeguard-20b", "gpt-oss", "safety-tuned"),
    ModelSpec("qwen3-32b", "groq", "qwen/qwen3-32b", "qwen"),
    # --- OpenRouter (paid, cents) ---
    ModelSpec("qwen2.5-coder-32b", "openrouter", "qwen/qwen-2.5-coder-32b-instruct", "qwen", "coder"),
    ModelSpec("mistral-small-24b", "openrouter", "mistralai/mistral-small-24b-instruct-2501", "mistral"),
    ModelSpec("deepseek-chat", "openrouter", "deepseek/deepseek-chat", "deepseek"),
    # --- Anthropic (frontier reference: measure refusal) ---
    ModelSpec("claude-haiku-4.5", "anthropic", "claude-haiku-4-5-20251001", "claude", "frontier"),
    ModelSpec("claude-sonnet-4.6", "anthropic", "claude-sonnet-4-6", "claude", "frontier"),
]
