from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    DATA_PATH: str
    NEW_VALUE: int

    model_config = SettingsConfigDict(
        env_file='config_local.py', extra='allow', case_sensitive=True)


settings = Settings()
