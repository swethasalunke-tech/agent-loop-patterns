# Build Schedule

This repo is being built incrementally, one pattern (or milestone) at a
time. Each day's work is only marked complete once it has real, passing
tests run locally (no fabricated output, no unverified claims).

## Day 1 (2026-08-24) — retry-with-critique pattern [this commit]

- `patterns/retry_with_critique.py`: generic, LLM-agnostic implementation.
- `tests/test_retry_with_critique.py`: 5 pytest tests using deterministic
  fake generate/critique functions (first-attempt success, fail-then-retry
  with feedback propagation verified precisely, exhausted attempts, and a
  `max_attempts=1` edge case, plus input validation).
- `examples/example_run.py`: offline runnable demo with toy functions.
- `DESIGN.md`, `README.md`, `requirements.txt`, `.gitignore`.

Status: done. `python3 -m pytest tests/ -v` passes (5/5) and
`python3 examples/example_run.py` runs to completion with exit code 0.

## Day 2 (planned) — plan-then-execute pattern

- `patterns/plan_then_execute.py`: a loop that first generates a plan
  (sequence of steps) for a prompt, then executes each step, with injected
  `plan` and `execute` functions (same dependency-injection approach as
  Day 1).
- `tests/test_plan_then_execute.py`: pytest tests with fake plan/execute
  functions, covering multi-step execution, a step failure/abort path, and
  edge cases (empty plan, single-step plan).
- Update `README.md` to list the new pattern.

## Day 3 (planned) — tool-use-with-verification pattern

- `patterns/tool_use_with_verification.py`: a loop where an agent proposes a
  tool call, the tool call is executed, and the result is verified before
  being accepted (with injected `propose_tool_call`, `execute_tool`, and
  `verify` functions).
- `tests/test_tool_use_with_verification.py`: pytest tests with fake tools
  and verifiers, covering a passing tool call, a failing/rejected tool call
  with retry, and exhaustion of attempts.
- Update `README.md` to list the new pattern.

## Day 4 (planned) — one real Anthropic-backed example

- Wire up **at least one** of the three patterns above to a real Anthropic
  API call, following the same structure as this account's
  `weekly-ai-tutor` repo (real API key from environment, real request/response,
  no invented sample output).
- If no Anthropic API key is available in the environment at the time this
  work is done, this will be documented honestly in that day's commit and
  README (e.g. "this example requires `ANTHROPIC_API_KEY`; it has not been
  live-tested in this environment") rather than fabricating sample output.
- This live-backed example is additive: it does not replace or modify the
  fake-function tests from Days 1–3, which remain the source of truth for
  testing the control-flow logic itself.
