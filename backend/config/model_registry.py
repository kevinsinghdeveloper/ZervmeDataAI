"""Static registry of available LLM models."""

LLM_MODELS = {
    # OpenAI
    "gpt-4o": {
        "provider": "openai",
        "model_name": "gpt-4o",
        "display_name": "GPT-4o",
        "max_context": 128000,
        "default_config": {"temperature": 0.7, "max_tokens": 4096},
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "display_name": "GPT-4o Mini",
        "max_context": 128000,
        "default_config": {"temperature": 0.7, "max_tokens": 4096},
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "model_name": "gpt-4-turbo",
        "display_name": "GPT-4 Turbo",
        "max_context": 128000,
        "default_config": {"temperature": 0.7, "max_tokens": 4096},
    },
    # Anthropic
    "claude-sonnet-4-5-20250929": {
        "provider": "anthropic",
        "model_name": "claude-sonnet-4-5-20250929",
        "display_name": "Claude Sonnet 4.5",
        "max_context": 200000,
        "default_config": {"temperature": 0.7, "max_tokens": 4096},
    },
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "model_name": "claude-3-5-haiku-20241022",
        "display_name": "Claude 3.5 Haiku",
        "max_context": 200000,
        "default_config": {"temperature": 0.7, "max_tokens": 4096},
    },
}


def get_llm_config(model_id: str) -> dict | None:
    """Get full config for a model by ID."""
    return LLM_MODELS.get(model_id)


def list_available_models() -> list[dict]:
    """Return list of all models with their metadata."""
    result = []
    for model_id, config in LLM_MODELS.items():
        result.append({"id": model_id, **config})
    return result


def get_provider_for_model(model_id: str) -> str | None:
    """Get the provider name for a model."""
    model = LLM_MODELS.get(model_id)
    return model["provider"] if model else None


def get_model_info(model_id: str) -> dict | None:
    """Get display info for a model."""
    model = LLM_MODELS.get(model_id)
    if not model:
        return None
    return {
        "id": model_id,
        "display_name": model["display_name"],
        "provider": model["provider"],
        "max_context": model["max_context"],
    }
