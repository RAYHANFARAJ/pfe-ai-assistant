from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    es_host: str
    es_username: str
    es_password: str

    index_xtra_campaign: str
    index_xtra_question: str
    index_xtra_choice: str
    index_account: str

    linkedin_email:    Optional[str] = None
    linkedin_password: Optional[str] = None
    proxycurl_api_key: Optional[str] = None

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2:1b"

    request_timeout: int = 60
    default_search_size: int = 1000
    max_question_size: int = 5000
    max_choice_size: int = 5000
    log_level: str = "INFO"

    keycloak_url: str = "http://localhost:8080"          # used for issuer validation (must match token)
    keycloak_internal_url: Optional[str] = None          # used for JWKS fetch (Docker internal address)
    keycloak_realm: str = "sellynx"

    model_config = SettingsConfigDict(
        # .env.local (if present) overrides .env — use it for local dev without VPN
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
