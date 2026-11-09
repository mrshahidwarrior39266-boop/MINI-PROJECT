"""The swap question must accept every realistic way a beginner writes three assignments."""
from pathlib import Path

import pytest

from app.services.question_service import QuestionService

ROOT = Path(__file__).resolve().parent.parent
QS = QuestionService(ROOT / "app" / "data" / "curriculum_questions.json")
SWAP_QUESTION = QS.questions["q_var_03"]

VALID_SWAPS = [
    # The reported case: three assignments separated only by spaces.
    "b=x x=y y=b",
    "b = x x = y y = b",
    "temp=x x=y y=temp",
    "t = x x = y y = t",
    "my_box=x x=y y=my_box",
    # Normal separators.
    "b=x; x=y; y=b",
    "b=x\nx=y\ny=b",
    "b=x, x=y, y=b",
    "b=x then x=y then y=b",
    "b = x, then x = y, then y = b",
    "use a temporary variable: temp = x, then x = y, then y = temp",
    # Prose / punctuation tails must not break executable code.
    "b=x x=y y=b and that swaps them",
    "b=x x=y y=b, then it is swapped",
    "b=x x=y y=b.",
    "b=x x=y y=b!",
    "b=x x=y y=b ",
    # Tuple unpacking (first/second are covered by the follow-up tests).
    "x, y = y, x",
    # Different helper-variable names and save order.
    "holding_area = y; y = x; x = holding_area",
    "third = x\nx = y\ny = third",
    "spare = x, x = y, y = spare",
    # Prose/code hybrids: a beginner may describe the first step and write the rest.
    "save x in temp, x = y, y = temp",
    "save y in temp, y = x, x = temp",
    "save 'x' into 'temp', then x = y, then y = temp",
    "save the value of x in temp, then x = y, then y = temp",
    "don't do x = y; save x in temp, x = y, y = temp",
    "temp = x is correct, then x = y, then y = temp",
    "put x in temp, put y in x, put temp in y",
    "assign x to temp, assign y to x, assign temp to y",
    "set temp to x, set x to y, set y to temp",
    "temp holds x, x holds y, y holds temp",
]

INVALID_SWAPS = [
    "x=y y=x",
    "x=y; y=x",
    "b=x x=y",
    "b=x x=y y=x",
    "b=x x=y y=z",
    "x=y and y=x",
    "save x in temp",
    "save x in temp, x = y",
    "x = y is wrong",
    "x = y is wrong; save x in temp, x = y",
]


def test_swap_rejects_arbitrary_python(tmp_path):
    marker = tmp_path / "executed.txt"
    code = f"x = __import__('pathlib').Path({str(marker)!r}).write_text('x')"
    result = QS.evaluate_main_question(SWAP_QUESTION, code)
    assert result.is_correct is False
    assert not marker.exists()
    assert "assignment" in result.feedback.lower()


def test_swap_rejects_attribute_access():
    result = QS.evaluate_main_question(SWAP_QUESTION, "x = print.__self__")
    assert result.is_correct is False


@pytest.mark.parametrize("answer", VALID_SWAPS)
def test_every_valid_swap_format_passes(answer):
    result = QS.evaluate_main_question(SWAP_QUESTION, answer)
    assert result.is_correct, f"Valid swap rejected: {answer!r} -> {result.feedback}"
    assert result.score == 1.0


@pytest.mark.parametrize("answer", INVALID_SWAPS)
def test_every_invalid_swap_format_fails(answer):
    result = QS.evaluate_main_question(SWAP_QUESTION, answer)
    assert result.is_correct is False, f"Invalid swap passed: {answer!r}"
    assert result.score == 0.0
