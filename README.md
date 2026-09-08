# agent-loop-patterns

A curated, tested library of runnable agent control-loop patterns —
implemented as real Python code and covered by real tests, not just
described in prose.

## Status

**Day 1.** Only the **retry-with-critique** pattern is implemented so far.
`plan-then-execute` and `tool-use-with-verification` are planned for later
days; see `BUILD-SCHEDULE.md`.

This repo currently tests pattern *logic* using deterministic fake
generate/critique functions. **Nothing here is wired to a real LLM yet.**
No live API calls are made anywhere in this repository, and no output in
it is a real model response — see `DESIGN.md` for why the loop is built
this way (dependency injection) and `BUILD-SCHEDULE.md` for when a real
Anthropic-backed example is planned.

## What's implemented

- `patterns/retry_with_critique.py` — generic `retry_with_critique(prompt,
  generate, critique, max_attempts=3)` control loop:
  - Calls `generate(prompt)`, then `critique(prompt, output)`.
  - Stops early if critique passes.
  - On failure, builds a new prompt that embeds the critique's feedback and
    retries, up to `max_attempts`.
  - Returns a `LoopResult` with `final_output`, `passed`, `attempts`, and
    full `history` of every (output, critique) pair.

## Running the tests

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

All tests use deterministic fake `generate`/`critique` functions defined
inline in the test file — there are no network calls and no live LLM
involved.

## Running the example

```bash
python3 examples/example_run.py
```

This runs `retry_with_critique` against a toy, fully offline `generate`
function (which simulates progressively improving drafts) and a toy
`critique` function (which checks output length and keyword presence).
It prints each attempt's output, critique feedback, and the final result,
and exits with status 0 on success / 1 if the loop never converged.

## Project layout

```
patterns/
  retry_with_critique.py   # the pattern implementation
tests/
  test_retry_with_critique.py
examples/
  example_run.py           # offline, runnable demo
DESIGN.md                  # scope and design rationale
BUILD-SCHEDULE.md          # day-by-day build plan
```
