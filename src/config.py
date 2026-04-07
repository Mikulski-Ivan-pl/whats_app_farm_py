from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    llm_api_key: str = Field(..., alias="LLM_API_KEY")
    cerebras_model: str = Field(..., alias="CEREBRAS_MODEL")
    system_prompt: str = Field(..., alias="SYSTEM_PROMPT")
    fallback_reply: str = Field(
        "Sorry, I couldn't generate a response right now. Please try again.",
        alias="FALLBACK_REPLY",
    )


settings = Settings()
