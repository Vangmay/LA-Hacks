from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    gemma_api_key: str = ""
    semantic_scholar_api_key: str = ""
    serpapi_api_key: str = ""
    serp_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = ""
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
    deepdive_dynamic_roster_enabled: bool = False
    deepdive_dynamic_roster_fallback_to_deterministic: bool = True
    deepdive_dynamic_roster_model_role: str = "investigator"
    deepdive_min_constructive_archetypes: int = 1
    deepdive_min_skeptical_archetypes: int = 1
    deepdive_min_prior_work_archetypes: int = 1
    deepdive_min_recent_future_archetypes: int = 1
    deepdive_max_duplicate_archetype_functions: int = 1
    deepdive_subagent_max_tool_calls: int = 24
    deepdive_investigator_max_rounds: int = 2
    deepdive_max_parallel_subagents: int = 8
    deepdive_stage_timeout_seconds: int = 900
    deepdive_default_search_limit: int = 25
    deepdive_report_detail_level: str = "extensive"
    deepdive_final_report_min_spinoff_proposals: int = 8
    deepdive_final_report_min_evidence_items_per_proposal: int = 3
    deepdive_final_report_min_open_questions: int = 10
    deepdive_critique_min_points_per_lens: int = 6
    deepdive_http_timeout_seconds: float = 60.0
    deepdive_model_timeout_seconds: float = 180.0
    deepdive_model_max_retries: int = 5
    deepdive_model_retry_max_delay_seconds: float = 90.0
    deepdive_tool_result_char_limit: int = 6000
    deepdive_workspace_write_char_budget: int = 3000
    deepdive_subagent_max_workspace_tool_calls: int = 1000
    deepdive_subagent_max_steps: int = 80
    deepdive_semantic_scholar_min_interval_seconds: float = 1.2
    deepdive_semantic_scholar_max_retries: int = 4
    deepdive_serpapi_max_requests: int = 50
    deepdive_llm_action_protocol: str = "json_action"
    deepdive_thinking_provider: str = "gemini_openai"
    deepdive_thinking_model: str = "gemma-4-26b-a4b-it"
    deepdive_thinking_api_key_env: str = "GEMMA_API_KEY"
    deepdive_thinking_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    deepdive_thinking_reasoning_effort: str = "high"
    deepdive_thinking_min_interval_seconds: float = 4.2
    deepdive_light_provider: str = "gemini_openai"
    deepdive_light_model: str = "gemma-4-26b-a4b-it"
    deepdive_light_api_key_env: str = "GEMMA_API_KEY"
    deepdive_light_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    deepdive_light_reasoning_effort: str = "high"
    deepdive_light_min_interval_seconds: float = 4.2
    deepdive_max_output_tokens_thinking: int = 16384
    deepdive_max_output_tokens_light: int = 16384

    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")


settings = Settings()
