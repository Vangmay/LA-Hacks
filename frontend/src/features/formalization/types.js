export const FORMALIZATION_EVENTS = {
  RUN_SNAPSHOT: 'run_snapshot',
  RUN_STARTED: 'run_started',
  ATOM_QUEUED: 'atom_queued',
  ATOM_CONTEXT_BUILT: 'atom_context_built',
  LLM_THOUGHT: 'llm_thought',
  TOOL_CALL_STARTED: 'tool_call_started',
  TOOL_CALL_COMPLETE: 'tool_call_complete',
  AXLE_CHECK_RESULT: 'axle_check_result',
  AXLE_VERIFY_RESULT: 'axle_verify_result',
  ARTIFACT_RECORDED: 'artifact_recorded',
  ARTIFACT_UPDATED: 'artifact_updated',
  ATOM_VERDICT: 'atom_verdict',
  ATOM_ERROR: 'atom_error',
  RUN_COMPLETE: 'run_complete',
  RUN_ERROR: 'run_error',
}

export const FORMALIZATION_LABELS = {
  FULLY_VERIFIED: 'fully_verified',
  CONDITIONALLY_VERIFIED: 'conditionally_verified',
  FORMALIZED_ONLY: 'formalized_only',
  DISPROVED: 'disproved',
  FORMALIZATION_FAILED: 'formalization_failed',
  NOT_A_THEOREM: 'not_a_theorem',
  GAVE_UP: 'gave_up',
}

export const TERMINAL_EVENTS = new Set([
  FORMALIZATION_EVENTS.RUN_COMPLETE,
  FORMALIZATION_EVENTS.RUN_ERROR,
])
