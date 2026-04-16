"""AI Service - Multi-provider chat with DynamoDB config, conversation context."""
import os
import json
from abstractions.IServiceManagerBase import IServiceManagerBase
from config.model_registry import LLM_MODELS, get_llm_config, list_available_models


DEFAULT_SYSTEM_PROMPT = (
    "You are an AI competitive intelligence assistant for Zerve DataAI. "
    "Help users analyze market data, generate competitive reports, "
    "and answer questions about brand positioning, industry trends, and strategic insights."
)


class AIService(IServiceManagerBase):
    def __init__(self, config=None):
        super().__init__(config)
        self._anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self._default_model = os.getenv("AI_MODEL", "claude-sonnet-4-5-20250929")
        self._system_prompt = DEFAULT_SYSTEM_PROMPT
        self._model_configs = {}  # DB overrides keyed by model_id
        self._max_conversation_history = 10
        self._db = None

    def set_db(self, db_service):
        self._db = db_service

    def initialize(self):
        if not self._anthropic_api_key and not self._openai_api_key:
            print("Warning: No AI API keys set. AI features will be limited.")
        self._load_config_from_db()

    def _load_config_from_db(self):
        """Load model configs and settings from config table."""
        if self._db is None:
            return
        try:
            # Load model overrides
            item = self._db.config.get_config("CONFIG", "ai_models")
            if item:
                data = item.get("data", item) if isinstance(item, dict) else getattr(item, "data", {})
                if isinstance(data, str):
                    import json
                    data = json.loads(data)
                self._model_configs = data.get("models", {}) if isinstance(data, dict) else {}

            # Load settings (system prompt, default model, max history)
            item = self._db.config.get_config("CONFIG", "settings")
            if item:
                data = item.get("data", item) if isinstance(item, dict) else getattr(item, "data", {})
                if isinstance(data, str):
                    import json
                    data = json.loads(data)
                if isinstance(data, dict):
                    if data.get("chatbotSystemPrompt"):
                        self._system_prompt = data["chatbotSystemPrompt"]
                    if data.get("defaultModel"):
                        self._default_model = data["defaultModel"]
                    if data.get("maxConversationHistory"):
                        self._max_conversation_history = int(data["maxConversationHistory"])
        except Exception as e:
            print(f"Warning: Could not load AI config from DB: {e}")

    def reload_config(self):
        """Re-read config from DynamoDB (called after admin saves)."""
        self._load_config_from_db()

    def chat(self, message: str, session_id: str, user_id: str,
             conversation_history: list = None, model_id: str = None) -> dict:
        """Send a chat message, routing to the correct provider."""
        effective_model = model_id or self._default_model
        model_config = self._get_effective_model_config(effective_model)

        if not model_config:
            return {"content": f"Model '{effective_model}' not found in registry.", "model_id": effective_model}

        provider = model_config["provider"]
        api_key = self._get_api_key(provider, effective_model)

        if not api_key:
            return {"content": f"No API key configured for {provider}. Set the API key in admin settings or environment variables.", "model_id": effective_model}

        # Build messages list from conversation history
        messages = []
        if conversation_history:
            for entry in conversation_history[-self._max_conversation_history:]:
                messages.append({"role": entry["role"], "content": entry["content"]})
        messages.append({"role": "user", "content": message})

        system_prompt = self._system_prompt

        try:
            if provider == "anthropic":
                result = self._chat_anthropic(messages, system_prompt, model_config, api_key)
            elif provider == "openai":
                result = self._chat_openai(messages, system_prompt, model_config, api_key)
            else:
                return {"content": f"Unknown provider: {provider}", "model_id": effective_model}

            result["model_id"] = effective_model
            return result
        except Exception as e:
            return {"content": f"AI error: {str(e)}", "model_id": effective_model}

    def _chat_anthropic(self, messages: list, system_prompt: str, model_config: dict, api_key: str) -> dict:
        """Call Anthropic API."""
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        config = model_config.get("config", model_config.get("default_config", {}))
        response = client.messages.create(
            model=model_config["model_name"],
            max_tokens=config.get("max_tokens", 4096),
            temperature=config.get("temperature", 0.7),
            system=system_prompt,
            messages=messages,
        )
        return {"content": response.content[0].text, "chart_config": None}

    def _chat_openai(self, messages: list, system_prompt: str, model_config: dict, api_key: str) -> dict:
        """Call OpenAI API."""
        import openai
        client = openai.OpenAI(api_key=api_key)
        config = model_config.get("config", model_config.get("default_config", {}))

        # OpenAI uses system message in the messages array
        openai_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model=model_config["model_name"],
            messages=openai_messages,
            max_tokens=config.get("max_tokens", 4096),
            temperature=config.get("temperature", 0.7),
        )
        return {"content": response.choices[0].message.content, "chart_config": None}

    def _get_api_key(self, provider: str, model_id: str) -> str:
        """Per-model key override -> env var fallback."""
        model_override = self._model_configs.get(model_id, {})
        # Check top-level api_key and nested config.api_key
        override_key = model_override.get("api_key", "") or model_override.get("config", {}).get("api_key", "")
        if override_key:
            return override_key

        if provider == "anthropic":
            return self._anthropic_api_key
        elif provider == "openai":
            return self._openai_api_key
        return ""

    def _get_effective_model_config(self, model_id: str) -> dict | None:
        """Merge static registry config with DynamoDB overrides, or return custom model."""
        base = get_llm_config(model_id)
        if base:
            # Registry model — merge with DynamoDB overrides
            result = dict(base)
            override = self._model_configs.get(model_id, {})
            if override.get("config"):
                merged_config = dict(base.get("default_config", {}))
                merged_config.update(override["config"])
                result["config"] = merged_config
            else:
                result["config"] = dict(base.get("default_config", {}))
            return result

        # Not in registry — check if it's a custom admin-added model
        custom = self._model_configs.get(model_id)
        if custom and custom.get("provider") and custom.get("model_name"):
            return {
                "provider": custom["provider"],
                "model_name": custom["model_name"],
                "display_name": custom.get("name", model_id),
                "max_context": int(custom.get("max_context", 128000)),
                "config": custom.get("config", {"temperature": 0.7, "max_tokens": 4096}),
            }

        return None

    def get_active_models(self) -> list:
        """Return list of all models with their config (API keys stripped)."""
        models = []
        seen_ids = set()

        # 1. Registry models (with DynamoDB overrides merged)
        for model_id, base in LLM_MODELS.items():
            seen_ids.add(model_id)
            override = self._model_configs.get(model_id, {})
            config = dict(base.get("default_config", {}))
            if override.get("config"):
                config.update(override["config"])

            # Only active if admin explicitly enabled AND has an API key
            has_api_key = bool(self._get_api_key(base["provider"], model_id))
            is_active = override.get("is_active", False) and has_api_key
            is_default = (model_id == self._default_model)

            models.append({
                "id": model_id,
                "name": override.get("name", base["display_name"]),
                "modelId": base["model_name"],
                "provider": base["provider"],
                "maxContext": base["max_context"],
                "isActive": is_active,
                "isDefault": is_default,
                "config": {
                    "temperature": float(config.get("temperature", 0.7)),
                    "maxTokens": int(config.get("max_tokens", 4096)),
                    "hasApiKey": has_api_key,
                },
            })

        # 2. Custom admin-added models (not in static registry)
        for model_id, custom in self._model_configs.items():
            if model_id in seen_ids:
                continue
            if not custom.get("provider") or not custom.get("model_name"):
                continue

            provider = custom["provider"]
            config = custom.get("config", {})
            has_api_key = bool(config.get("api_key") or self._get_api_key(provider, model_id))
            is_active = custom.get("is_active", False) and has_api_key

            models.append({
                "id": model_id,
                "name": custom.get("name", model_id),
                "modelId": custom["model_name"],
                "provider": provider,
                "maxContext": int(custom.get("max_context", 128000)),
                "isActive": is_active,
                "isDefault": (model_id == self._default_model),
                "config": {
                    "temperature": float(config.get("temperature", 0.7)),
                    "maxTokens": int(config.get("max_tokens", 4096)),
                    "hasApiKey": has_api_key,
                },
                "createdAt": custom.get("created_at"),
                "updatedAt": custom.get("updated_at"),
            })

        return models

    def update_model_config(self, model_id: str, config_data: dict) -> dict:
        """Save model config to DB. Supports both registry overrides and new custom models."""
        from datetime import datetime

        # Load existing
        item = self._db.config.get_config("CONFIG", "ai_models")
        if item:
            data = item.get("data", item) if isinstance(item, dict) else getattr(item, "data", {})
            if isinstance(data, str):
                data = json.loads(data)
            models = data.get("models", {}) if isinstance(data, dict) else {}
        else:
            models = {}

        existing = models.get(model_id, {})
        now = datetime.utcnow().isoformat()

        # Full model definition (from JSON config editor / create flow)
        if "name" in config_data:
            existing["name"] = config_data["name"]
        if "provider" in config_data:
            existing["provider"] = config_data["provider"]
        if "model_name" in config_data:
            existing["model_name"] = config_data["model_name"]
        elif "modelId" in config_data and "model_name" not in existing:
            existing["model_name"] = config_data["modelId"]
        if "max_context" in config_data:
            existing["max_context"] = int(config_data["max_context"])

        # Active flag
        if "is_active" in config_data:
            existing["is_active"] = config_data["is_active"]
        elif "isActive" in config_data:
            existing["is_active"] = config_data["isActive"]

        # JSON config (api_key, temperature, max_tokens, etc.)
        if "config" in config_data:
            if isinstance(config_data["config"], str):
                try:
                    existing["config"] = json.loads(config_data["config"])
                except json.JSONDecodeError:
                    existing["config"] = existing.get("config", {})
            else:
                existing["config"] = config_data["config"]

        # Legacy field-level overrides (backward compat with old UI)
        if "apiKey" in config_data and config_data["apiKey"]:
            cfg = existing.get("config", {})
            cfg["api_key"] = config_data["apiKey"]
            existing["config"] = cfg

        # Default model
        if config_data.get("isDefault"):
            self._default_model = model_id
            self._save_default_model(model_id)

        # Timestamps
        if "created_at" not in existing:
            existing["created_at"] = now
        existing["updated_at"] = now

        models[model_id] = existing
        self._db.config.put_config("CONFIG", "ai_models", {"models": models})

        # Update in-memory cache
        self._model_configs = models
        return {"success": True, "message": f"Model {model_id} config updated"}

    def _save_default_model(self, model_id: str):
        """Update the defaultModel in settings."""
        try:
            item = self._db.config.get_config("CONFIG", "settings")
            if item:
                data = item.get("data", item) if isinstance(item, dict) else getattr(item, "data", {})
                if isinstance(data, str):
                    data = json.loads(data)
            else:
                data = {}
            data["defaultModel"] = model_id
            self._db.config.put_config("CONFIG", "settings", data)
        except Exception:
            pass

    def delete_model_config(self, model_id: str) -> dict:
        """Remove model override from DB (revert to registry defaults)."""
        item = self._db.config.get_config("CONFIG", "ai_models")
        if item:
            data = item.get("data", item) if isinstance(item, dict) else getattr(item, "data", {})
            if isinstance(data, str):
                data = json.loads(data)
            models = data.get("models", {}) if isinstance(data, dict) else {}
        else:
            models = {}

        if model_id in models:
            del models[model_id]
            self._db.config.put_config("CONFIG", "ai_models", {"models": models})
            self._model_configs = models

        return {"success": True, "message": f"Model {model_id} config reset to defaults"}

