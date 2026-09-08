# Design

## Scope (Day 1)

This repository is a curated, tested library of runnable agent control-loop
patterns, implemented as real Python code rather than prose/documentation.

Day 1 implements exactly one pattern: **retry-with-critique**.

- `patterns/retry_with_critique.py` — the loop implementation.
- `tests/test_retry_with_critique.py` — pytest tests using deterministic
  fake `generate`/`critique` functions (no live LLM calls).
- `examples/example_run.py` — an offline, runnable demonstration using toy
  in-process functions (no external API calls).

## Design principle: LLM-agnostic via dependency injection

`retry_with_critique` takes `generate` and `critique` as injected callables:

```python
GenerateFn = Callable[[str], str]
CritiqueFn = Callable[[str, str], CritiqueResult]
```

The loop itself contains no knowledge of any specific LLM provider, prompt
format, or API. This is deliberate:

- It makes the control-flow logic fully unit-testable with fake functions,
  which is what this repo actually does in `tests/`.
- It means the same loop can later be wired to a real model (e.g. the
  Anthropic API) simply by supplying real `generate`/`critique`
  implementations, without changing the loop itself.
- It keeps the pattern's logic (retry, feedback propagation, stopping
  conditions) separate from any concerns about token usage, API errors,
  rate limits, or prompt engineering, which belong in the injected
  functions, not the loop.

## What the loop actually does

1. Call `generate(prompt)`.
2. Call `critique(prompt, output)`.
3. If `critique.passed`, stop and return.
4. Otherwise, if attempts remain, build a new prompt that embeds the
   critique's feedback and call `generate` again.
5. Stop after `max_attempts` attempts regardless of outcome.

The returned `LoopResult` includes the full `history` of every
(output, critique) pair, not just the final one, so callers (and tests) can
inspect exactly what happened at each attempt.

## Explicitly deferred (not built yet)

The following are intentionally **out of scope for Day 1** and are not
present in this repository yet:

- **plan-then-execute pattern** — deferred to Day 2.
- **tool-use-with-verification pattern** — deferred to Day 3.
- **A real Anthropic-backed example** wired up the way this account's
  `weekly-ai-tutor` repo wires up a live model — deferred to Day 4. Nothing
  in this repository currently makes a live API call, and no live-verified
  output is claimed anywhere in it. `examples/example_run.py` uses toy,
  offline functions only.

See `BUILD-SCHEDULE.md` for the day-by-day plan.
