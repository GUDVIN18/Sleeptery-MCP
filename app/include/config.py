from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Config(BaseSettings):
    DOCKER_SECRET: str = Field(validation_alias='DOCKER_SECRET')
    LOG_LEVEL: str = Field(validation_alias='LOG_LEVEL')

    # URLS
    ST_SLEEP_URL: str = Field(validation_alias='ST_SLEEP_URL')
    ST_DIARY_URL: str = Field(validation_alias='ST_DIARY_URL')
    ST_ACCOUNT_MANAGER_URL: str = Field(validation_alias='ST_ACCOUNT_MANAGER_URL')

    QWEN_API_KEY: str = Field(None, validation_alias='QWEN_API_KEY')
    MODEL_SLEEP_AI: str = Field(None, validation_alias='MODEL_SLEEP_AI')
    MCP_URL: str = Field(None, validation_alias='MCP_URL')

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

config = Config()
