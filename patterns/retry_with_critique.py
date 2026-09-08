"""
retry_with_critique
====================

A generic, LLM-agnostic implementation of the "retry with critique" agent
control-loop pattern:

    1. Generate an output for a prompt.
    2. Critique that output.
    3. If the critique passes, stop and return the result.
    4. If it fails, feed the critique's feedback back into the next
       generation attempt, and retry (up to a maximum number of attempts).

The `generate` and `critique` functions are injected by the caller, so this
module has no dependency on any particular LLM provider or API. That makes
it trivially testable with fake/deterministic functions (see
tests/test_retry_with_critique.py) and reusable with any real generator or
critique implementation later (e.g. an Anthropic-backed one).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Protocol, Tuple


@dataclass
class CritiqueResult:
    """Result of critiquing a single generated output.

    Attributes:
        passed: Whether the output satisfies the critique's criteria.
        feedback: Human-readable feedback describing what's wrong (or, if
            passed, may simply confirm success). This feedback is what gets
            passed back into the next `generate` call on retry.
    """

    passed: bool
    feedback: str


# A generate function takes a prompt (which may already include feedback
# context appended by the loop) and returns generated text.
GenerateFn = Callable[[str], str]

# A critique function takes (prompt, output) and returns a CritiqueResult.
CritiqueFn = Callable[[str, str], CritiqueResult]


class GenerateProtocol(Protocol):
    def __call__(self, prompt: str) -> str: ...


class CritiqueProtocol(Protocol):
    def __call__(self, prompt: str, output: str) -> CritiqueResult: ...


@dataclass
class LoopResult:
    """Final result of running the retry_with_critique loop.

    Attributes:
        final_output: The last generated output (whether or not it passed).
        passed: Whether the final output passed critique.
        attempts: Number of generate/critique attempts actually made.
        history: List of (output, critique_result) pairs, one per attempt,
            in order. `len(history) == attempts`.
    """

    final_output: str
    passed: bool
    attempts: int
    history: List[Tuple[str, CritiqueResult]] = field(default_factory=list)


def _build_retry_prompt(original_prompt: str, feedback: str) -> str:
    """Build the prompt used for a retry attempt, incorporating feedback.

    This is intentionally simple and explicit so tests can assert on the
    exact prompt text passed into `generate`.
    """
    return (
        f"{original_prompt}\n\n"
        f"Previous attempt did not pass critique. Feedback:\n{feedback}\n"
        f"Please revise your output to address this feedback."
    )


def retry_with_critique(
    prompt: str,
    generate: GenerateFn,
    critique: CritiqueFn,
    max_attempts: int = 3,
) -> LoopResult:
    """Run the retry-with-critique control loop.

    On attempt 1, calls `generate(prompt)`. If critique fails and more
    attempts remain, subsequent calls use a prompt that embeds the prior
    critique's feedback (built via `_build_retry_prompt`), so the generator
    has a chance to actually address what was wrong.

    Stops as soon as a critique passes, or after `max_attempts` attempts,
    whichever comes first.

    Args:
        prompt: The original task prompt.
        generate: Callable that produces an output string given a prompt.
        critique: Callable that evaluates (prompt, output) and returns a
            CritiqueResult.
        max_attempts: Maximum number of generate/critique attempts (must be
            >= 1).

    Returns:
        LoopResult summarizing the outcome.

    Raises:
        ValueError: If max_attempts < 1.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    history: List[Tuple[str, CritiqueResult]] = []
    current_prompt = prompt
    output = ""
    result = CritiqueResult(passed=False, feedback="")

    for attempt in range(1, max_attempts + 1):
        output = generate(current_prompt)
        result = critique(prompt, output)
        history.append((output, result))

        if result.passed:
            break

        # Prepare the prompt for the next attempt (if any remain).
        current_prompt = _build_retry_prompt(prompt, result.feedback)

    return LoopResult(
        final_output=output,
        passed=result.passed,
        attempts=len(history),
        history=history,
    )
