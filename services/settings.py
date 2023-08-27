from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    DATA_PATH: str

    model_config = SettingsConfigDict(env_file='config_local.py', case_sensitive=True)


settings = Settings()
