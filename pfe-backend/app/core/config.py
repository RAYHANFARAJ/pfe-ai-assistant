from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    es_host: str
    es_username: str
    es_password: str

    index_xtra_campaign: str
    index_xtra_question: str
    index_xtra_choice: str
    index_account: str

    request_timeout: int = 60
    default_search_size: int = 1000
    max_question_size: int = 5000
    max_choice_size: int = 5000
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        # .env.local (if present) overrides .env — use it for local dev without VPN
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
