from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    backend_port: int = 8000
    frontend_port: int = 5173
    max_parallel_claims: int = 5
    attacker_challenge_cap: int = 3
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
