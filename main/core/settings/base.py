from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """
    Base application setting class.
    """

    model_config = SettingsConfigDict(env_file=".env", extra='allow')
