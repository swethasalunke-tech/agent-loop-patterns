"""
example_run.py
===============

A small, fully offline, runnable demonstration of the retry_with_critique
pattern. There are NO external API calls here -- `generate` and `critique`
are both toy in-process functions, so this script is deterministic and safe
to run anywhere with just the standard library plus this repo.

`generate` simulates an LLM that writes progressively better drafts on each
retry (it uses the feedback embedded in the prompt to decide how to
improve). `critique` checks two simple, concrete conditions: minimum length
and presence of a required keyword.

Run with:
    python3 examples/example_run.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from patterns.retry_with_critique import CritiqueResult, retry_with_critique

REQUIRED_KEYWORD = "agent-loop-patterns"
MIN_LENGTH = 60


def toy_generate(prompt: str) -> str:
    """A toy stand-in for an LLM call.

    This is NOT a real language model. It's a simple deterministic function
    that inspects the prompt to decide how "good" a draft to produce, so the
    example can demonstrate the retry loop actually improving output across
    attempts without calling any external service.
    """
    if "Feedback" not in prompt:
        # First attempt: deliberately weak draft (too short, missing keyword).
        return "This is a short draft."

    if "too short" in prompt.lower():
        # Second attempt: longer, but still missing the required keyword.
        return (
            "This draft has been expanded significantly to address the "
            "length feedback from the previous critique, but it still "
            "does not mention the project by name."
        )

    # Third attempt: long enough AND mentions the keyword.
    return (
        f"This final draft describes the {REQUIRED_KEYWORD} project in "
        "enough detail to satisfy both the length and keyword "
        "requirements set by the critique function."
    )


def toy_critique(prompt: str, output: str) -> CritiqueResult:
    """A toy stand-in for an LLM-based critique.

    Checks two concrete, mechanically verifiable conditions:
      1. Output is at least MIN_LENGTH characters long.
      2. Output mentions REQUIRED_KEYWORD.
    """
    problems = []

    if len(output) < MIN_LENGTH:
        problems.append(
            f"Output is too short ({len(output)} chars); needs at least "
            f"{MIN_LENGTH} characters."
        )

    if REQUIRED_KEYWORD not in output:
        problems.append(
            f"Output must mention the keyword '{REQUIRED_KEYWORD}'."
        )

    if problems:
        return CritiqueResult(passed=False, feedback=" ".join(problems))

    return CritiqueResult(passed=True, feedback="Meets length and keyword requirements.")


def main() -> None:
    prompt = "Write a short description of this project."

    result = retry_with_critique(
        prompt=prompt,
        generate=toy_generate,
        critique=toy_critique,
        max_attempts=3,
    )

    print("=== retry_with_critique example run ===")
    print(f"Prompt: {prompt}")
    print()

    for i, (output, critique_result) in enumerate(result.history, start=1):
        status = "PASSED" if critique_result.passed else "FAILED"
        print(f"--- Attempt {i}: {status} ---")
        print(f"Output:   {output}")
        print(f"Feedback: {critique_result.feedback}")
        print()

    print("=== Final result ===")
    print(f"Passed:   {result.passed}")
    print(f"Attempts: {result.attempts}")
    print(f"Final output: {result.final_output}")

    if not result.passed:
        # Exit non-zero if the loop never converged, so this script can be
        # used as a real smoke test / CI check, not just a demo.
        sys.exit(1)


if __name__ == "__main__":
    main()
