import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openweather_api_key: str = ""
    google_api_key: str = ""
    jolpica_base: str = "https://api.jolpi.ca/ergast/f1"
    cache_db_path: str = ""          # default resolved at runtime
    fastf1_cache_dir: str = ""       # default resolved at runtime
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def resolved_cache_db(self) -> str:
        if self.cache_db_path:
            return self.cache_db_path
        return os.path.join(os.path.dirname(__file__), "..", "data", "cache.db")

    def resolved_fastf1_dir(self) -> str:
        if self.fastf1_cache_dir:
            return self.fastf1_cache_dir
        return os.path.join(os.path.dirname(__file__), "..", "cache")


settings = Settings()
