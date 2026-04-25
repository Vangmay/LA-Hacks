from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    backend_port: int = 8000
    frontend_port: int = 5173
    max_parallel_claims: int = 5
    attacker_challenge_cap: int = 3
    log_level: str = "INFO"
    deepdive_workspace_root: str = "backend/outputs/research_deepdives"
    deepdive_max_investigators: int = 4
    deepdive_subagents_per_investigator: int = 5
    deepdive_min_personas_per_investigator: int = 4
    deepdive_max_personas_per_investigator: int = 7
    deepdive_require_persona_diversity: bool = True
    deepdive_subagent_max_tool_calls: int = 24
    deepdive_investigator_max_rounds: int = 2
    deepdive_max_parallel_subagents: int = 8
    deepdive_stage_timeout_seconds: int = 900
    deepdive_default_search_limit: int = 25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
