from pathlib import Path

from app.services.question_service import QuestionService

ROOT = Path(__file__).resolve().parent.parent
QS = QuestionService(ROOT / "app" / "data" / "curriculum_questions.json")
SWAP_QUESTION = QS.questions["q_var_03"]


def test_pure_logic_variable_agnostic_swapping():
    # Every one of these is logically sound, even though variable names and order differ
    valid_variations = [
        "t=x,x=y,y=t",
        "temp = x; x = y; y = temp",
        "my_box = x\nx = y\ny = my_box",
        "holding_area = y; y = x; x = holding_area",  # Saving y first instead of x
        "x, y = y, x",
        "z = x, x = y, y = z",
    ]

    for code in valid_variations:
        res = QS.evaluate_main_question(SWAP_QUESTION, code)
        assert res.is_correct is True, f"Failed for valid logic: {code}"
        assert res.score == 1.0


def test_buggy_swap_logic_fails():
    # Both of these are logically flawed
    flawed = [
        "x = y; y = x",              # overwrites x immediately
        "x = a; a = b; b = y",       # undefined variable 'a', unused y
        "first = temp; temp = second; second = first",  # wrong direction
    ]

    for code in flawed:
        res = QS.evaluate_main_question(SWAP_QUESTION, code)
        assert res.is_correct is False, f"Buggy logic passed when it should fail: {code}"
