from abstractions.enumerations.AiTypeEnum import AiTypeEnum


ai_service_map = {
    AiTypeEnum.OpenAI.value: AiTypeEnum.OpenAI,
}


class AIServiceHandler:
    @staticmethod
    def get_ai_service(llm_config: dict):
        ai_type = llm_config.get("ai_type")
        if ai_type not in ai_service_map:
            supported_types = list(ai_service_map.keys())
            raise ValueError(
                f"Unsupported AI type: {ai_type}. "
                f"Supported types are: {supported_types}")

        ai_enum = ai_service_map[ai_type]

        if ai_enum == AiTypeEnum.OpenAI:
            from services.ai.OpenAIETLServiceManager import OpenAIETLServiceManager
            llm_manager = OpenAIETLServiceManager(llm_config)
            llm_manager.configure()
            return llm_manager

        raise NotImplementedError(f"AI type {ai_type} not implemented")
