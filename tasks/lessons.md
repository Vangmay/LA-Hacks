# Lessons

- Do not demonstrate the AXLE formalization loop with tiny caps and present the
  result as representative. The point of the feature is iterative repair:
  AXLE feedback must be fed back to the agent repeatedly until the spec
  compiles, the proof verifies, or a very high operational guard is exhausted.
- Do not allow `formalized_only` unless AXLE has actually returned `okay=true`
  for a faithful spec. Recorded Lean text alone is not enough.
- AXLE compiles syntactic Lean. It cannot tell whether a proof is *faithful*
  to the paper claim. The model can satisfy `axle_check` + `axle_verify_proof`
  with vacuous encodings: `theorem T : ∃ x : Type, True := ⟨Unit, trivial⟩`,
  `def isFoo := False; theorem ¬ isFoo := by simp`, or
  `def x = expr; theorem x = expr := by rfl`. The system prompt now bans these
  patterns explicitly; without that, "fully_verified" silently means nothing.
- For multi-atom runs, OpenAI's per-organization TPM (30k for gpt-4o on the
  default tier) is the bottleneck, not Lean. With `parallelism=3`, two atoms
  out of fourteen got killed by 429s on the VAE paper. Drop to `parallelism=2`
  and bump the agent's rate-limit retry cap to ≥16 with jittered delays.
- When running long Python jobs in the background, redirect to a file with
  `python -u` (or `PYTHONUNBUFFERED=1`) so stdout flushes per-line; otherwise
  the file lags behind real progress and `tail -F` makes more sense than
  `grep` on the file.
- Never launch a long backend script via Bash with `&` inside
  `run_in_background: true`. The shell exits immediately and the worker dies.
  Use `run_in_background: true` with a plain redirect, no `&`.
