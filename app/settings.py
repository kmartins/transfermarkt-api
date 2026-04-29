from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    RATE_LIMITING_ENABLE: bool = False
    RATE_LIMITING_FREQUENCY: str = "2/3seconds"
    SCRAPERAPI_KEY: str = ""
    CACHE_ENABLE: bool = True
    CACHE_TTL: int = 43200
    CACHE_MAXSIZE: int = 200


settings = Settings()
