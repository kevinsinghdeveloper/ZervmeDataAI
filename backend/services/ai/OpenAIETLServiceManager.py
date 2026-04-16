import json
import logging

from openai import OpenAI

from abstractions.ILLMServiceManager import ILLMServiceManager
from models.request.LLMRequestResourceModel import LLMRequestResourceModel
from models.response.LLMResponseResourceModel import LLMResponseResourceModel


class OpenAIETLServiceManager(ILLMServiceManager):
    def __init__(self, config: dict):
        super().__init__(config)
        self.__model_name = None
        self.__genai_config = None
        self.__model = None

    def configure(self, **kwargs) -> None:
        config = self._config
        api_key = config["api_key"]
        self.__model = OpenAI(api_key=api_key)
        self.__genai_config = config.get('gen_config', {})
        self.__model_name = config['model_name']

    def get_base_prompt(self, prompt: str, llm_instructions: str):
        system_prompt = {"role": "system", "content": llm_instructions}
        base_prompt = {"role": "user", "content": prompt}
        return system_prompt, base_prompt

    def run_task(self, request_resource_model: LLMRequestResourceModel) -> LLMResponseResourceModel:
        history_messages = request_resource_model.history_messages or []
        messages = [
            {"role": "system", "content": request_resource_model.system_prompt}
        ] + history_messages

        if not any(m["role"] == "user" for m in history_messages):
            messages.append({"role": "user", "content": request_resource_model.prompt})

        response_type = request_resource_model.response_type or "str"

        response = self.__model.chat.completions.create(
            model=self.__model_name,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=self.__genai_config.get("temperature", 1),
            max_tokens=self.__genai_config.get("max_output_tokens", 500)
        )

        cleaned_response = response.choices[0].message.content
        usage = response.usage

        new_history = history_messages + [
            {"role": "assistant", "content": cleaned_response}
        ]

        if response_type == "dict":
            try:
                cleaned_response = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logging.warning(f"Failed to parse response as JSON: {e}")
                raise ValueError("Invalid JSON returned by model.")

        return LLMResponseResourceModel(
            response_content=cleaned_response,
            history_messages=new_history,
            usage_data={"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens, "total_tokens": usage.total_tokens} if usage else None
        )

    def initialize(self):
        pass
