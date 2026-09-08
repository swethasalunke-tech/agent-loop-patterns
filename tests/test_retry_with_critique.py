"""
Real pytest tests for retry_with_critique, using deterministic fake
generate/critique functions. No live LLM calls are made anywhere in this
file.
"""

import sys
from pathlib import Path

# Make the `patterns` package importable without requiring installation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from patterns.retry_with_critique import (
    CritiqueResult,
    LoopResult,
    retry_with_critique,
)


def test_succeeds_on_first_attempt():
    """If critique passes immediately, the loop should stop after 1 attempt
    and not call generate again."""

    generate_calls = []

    def generate(prompt: str) -> str:
        generate_calls.append(prompt)
        return "a fine answer"

    def critique(prompt: str, output: str) -> CritiqueResult:
        return CritiqueResult(passed=True, feedback="looks good")

    result = retry_with_critique(
        prompt="write something",
        generate=generate,
        critique=critique,
        max_attempts=3,
    )

    assert isinstance(result, LoopResult)
    assert result.passed is True
    assert result.attempts == 1
    assert result.final_output == "a fine answer"
    assert len(result.history) == 1
    assert result.history[0][0] == "a fine answer"
    assert result.history[0][1].passed is True
    assert len(generate_calls) == 1
    assert generate_calls[0] == "write something"


def test_fails_first_then_succeeds_and_feedback_is_passed_to_second_generate():
    """Critical behavior: the feedback from the FIRST critique must actually
    show up in the prompt passed to the SECOND generate call. We assert on
    the exact prompt text, not just that the loop eventually passes."""

    generate_calls = []

    def generate(prompt: str) -> str:
        generate_calls.append(prompt)
        if len(generate_calls) == 1:
            return "too short"
        return "a sufficiently long and detailed answer"

    def critique(prompt: str, output: str) -> CritiqueResult:
        if len(output) < 20:
            return CritiqueResult(
                passed=False,
                feedback="Output is too short; needs at least 20 characters.",
            )
        return CritiqueResult(passed=True, feedback="Length is sufficient.")

    result = retry_with_critique(
        prompt="describe the pattern",
        generate=generate,
        critique=critique,
        max_attempts=3,
    )

    # Loop outcome.
    assert result.passed is True
    assert result.attempts == 2
    assert result.final_output == "a sufficiently long and detailed answer"
    assert len(result.history) == 2

    # First attempt used the original prompt untouched.
    assert generate_calls[0] == "describe the pattern"

    # Second attempt's prompt must contain the exact feedback text from the
    # first critique -- this is the crux of the pattern.
    second_prompt = generate_calls[1]
    assert "Output is too short; needs at least 20 characters." in second_prompt
    assert "describe the pattern" in second_prompt

    # History should record both attempts with correct pass/fail flags.
    assert result.history[0][0] == "too short"
    assert result.history[0][1].passed is False
    assert result.history[1][0] == "a sufficiently long and detailed answer"
    assert result.history[1][1].passed is True


def test_exhausts_all_attempts_without_passing():
    """If critique never passes, the loop must stop at max_attempts, report
    passed=False, and retain the full history of every attempt."""

    generate_calls = []

    def generate(prompt: str) -> str:
        generate_calls.append(prompt)
        return f"attempt {len(generate_calls)}"

    def critique(prompt: str, output: str) -> CritiqueResult:
        return CritiqueResult(passed=False, feedback=f"still wrong: {output}")

    result = retry_with_critique(
        prompt="do the impossible",
        generate=generate,
        critique=critique,
        max_attempts=3,
    )

    assert result.passed is False
    assert result.attempts == 3
    assert len(generate_calls) == 3
    assert len(result.history) == 3

    # Final output is the last attempt's output.
    assert result.final_output == "attempt 3"

    # Full history present and in order, all failed.
    for i, (output, critique_result) in enumerate(result.history, start=1):
        assert output == f"attempt {i}"
        assert critique_result.passed is False
        assert critique_result.feedback == f"still wrong: attempt {i}"

    # Confirm feedback propagation continued across every retry, not just
    # the first one.
    assert "still wrong: attempt 1" in generate_calls[1]
    assert "still wrong: attempt 2" in generate_calls[2]


def test_max_attempts_one_edge_case():
    """With max_attempts=1, only a single generate/critique call should
    happen, even if it fails -- no retry should be attempted."""

    generate_calls = []

    def generate(prompt: str) -> str:
        generate_calls.append(prompt)
        return "only try"

    def critique(prompt: str, output: str) -> CritiqueResult:
        return CritiqueResult(passed=False, feedback="never good enough")

    result = retry_with_critique(
        prompt="one shot",
        generate=generate,
        critique=critique,
        max_attempts=1,
    )

    assert result.attempts == 1
    assert result.passed is False
    assert len(generate_calls) == 1
    assert generate_calls[0] == "one shot"
    assert len(result.history) == 1
    assert result.final_output == "only try"


def test_max_attempts_must_be_at_least_one():
    """max_attempts < 1 is invalid and should raise ValueError."""

    def generate(prompt: str) -> str:
        return "x"

    def critique(prompt: str, output: str) -> CritiqueResult:
        return CritiqueResult(passed=True, feedback="ok")

    import pytest

    with pytest.raises(ValueError):
        retry_with_critique(
            prompt="p",
            generate=generate,
            critique=critique,
            max_attempts=0,
        )
