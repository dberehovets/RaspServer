import os.path

from pydantic_core import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ROOT_DIR: str = os.path.dirname(__file__)

    DATA_PATH: str

    _CONFIG_FILE_NAME: str = 'config_local.py'

    model_config = SettingsConfigDict(env_file=_CONFIG_FILE_NAME, case_sensitive=True)

    def __init__(self):
        try:
            super().__init__()
        except ValidationError:
            keys = [v for v in self.model_fields.keys() if not v.startswith("_")]
            print('\033[91mAdd config_local.py file at the root of the project and add to it the '
                  f'following fields: {", ".join(keys)}')
            exit()


settings = Settings()
