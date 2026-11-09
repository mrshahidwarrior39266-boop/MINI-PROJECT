"""Regression tests for the grading engine, using realistic beginner answers."""
from pathlib import Path

import pytest

from app.services.question_service import QuestionService

ROOT = Path(__file__).resolve().parent.parent
QS = QuestionService(ROOT / "app" / "data" / "curriculum_questions.json")


def status(result) -> str:
    if result.is_correct and result.score == 1.0:
        return "full"
    if not result.is_correct and result.score > 0:
        return "partial"
    return "wrong"


MAIN_CASES = [
    # Variables: assignment vs equality
    ("q_var_01", "Python evaluates the right side (x + 1) first using the current value of x, and then binds that new resulting value back to the label x on the left.", "full"),
    ("q_var_01", "the right side x + 1 is calculated first, then the result is assigned to x", "full"),
    ("q_var_01", "x gets 6 if x was 5", "full"),
    ("q_var_01", "it is not algebra: = assigns the value on the right to x", "full"),
    ("q_var_01", "it means x equals x plus one, impossible", "wrong"),
    ("q_var_01", "no solution", "wrong"),
    ("q_var_01", "assign", "partial"),
    ("q_var_01", "idk", "wrong"),
    # Variables: copied value vs permanent link
    ("q_var_02", "b is 10 because b got a copy of a's value when it was 10", "full"),
    ("q_var_02", "10, since changing a to 20 later doesn't affect b", "full"),
    ("q_var_02", "b is 10, not 20", "partial"),
    ("q_var_02", "b is 10; a is 20 now", "partial"),
    ("q_var_02", "b is 10 because it is not linked to a", "full"),
    ("q_var_02", "b is 20 because a changed", "wrong"),
    ("q_var_02", "b is 20, since it copies a", "wrong"),
    ("q_var_02", "they are linked", "wrong"),
    # Variables: swap
    ("q_var_03", "temp = x; x = y; y = temp", "full"),
    ("q_var_03", "x, y = y, x", "full"),
    ("q_var_03", "use a temporary variable: temp = x, then x = y, then y = temp", "full"),
    ("q_var_03", "save x in temp, copy y into x, then put temp into y", "full"),
    ("q_var_03", "use a temporary variable to save x", "partial"),
    ("q_var_03", "x = y; y = x", "wrong"),
    ("q_var_03", "temp = x; x = y; y = templ", "wrong"),
    ("q_var_03", "just x = y then y = x", "wrong"),
    # Data types: string concatenation
    ("q_types_01", "It outputs '55'. Quotation marks define text strings (str), and the '+' operator concatenates (glues) strings together rather than performing math.", "full"),
    ("q_types_01", "it prints 55 because they are strings, so + glues them together", "full"),
    ("q_types_01", "it's not 10, it's 55 because strings are glued", "full"),
    ("q_types_01", "55", "partial"),
    ("q_types_01", "string", "partial"),
    ("q_types_01", "10", "wrong"),
    ("q_types_01", "it prints 10 because 5+5=10", "wrong"),
    # Data types: conversion
    ("q_types_02", "Use int(age), for example: age = int(age)", "full"),
    ("q_types_02", "int(age)", "full"),
    ("q_types_02", "use the int() function to convert it", "full"),
    ("q_types_02", "int", "partial"),
    ("q_types_02", "str(age)", "wrong"),
    ("q_types_02", "print(age)", "wrong"),
    ("q_types_02", "leave it, python will convert it automatically", "wrong"),
    # Operators
    ("q_ops_01", "7 / 2 returns 3.5 (float division), while 7 // 2 returns 3 (floor division, discarding the fractional part).", "full"),
    ("q_ops_01", "7 / 2 gives 3.5 while 7 // 2 gives 3", "full"),
    ("q_ops_01", "single slash returns a float decimal, double slash floors it to 3", "full"),
    ("q_ops_01", "3.5 and 3", "full"),
    ("q_ops_01", "single slash returns a float", "partial"),
    ("q_ops_01", "both return 3", "wrong"),
    ("q_ops_01", "both are 3.5", "wrong"),
    ("q_ops_01", "7/2 is 3 and 7//2 is 3.5", "wrong"),
    # Conditionals
    ("q_cond_01", "Multiple 'if' statements are evaluated independently, so several can run. In an 'elif' chain, branches are mutually exclusive; once one condition is True, all remaining branches are skipped.", "full"),
    ("q_cond_01", "multiple ifs all get checked, while an elif chain stops after the first true one", "full"),
    ("q_cond_01", "with separate ifs more than one block can run; elif only runs one", "full"),
    ("q_cond_01", "they are mutually exclusive: only the first matching branch runs", "partial"),
    ("q_cond_01", "they are not the same thing: separate ifs can all run", "partial"),
    ("q_cond_01", "same thing", "wrong"),
    ("q_cond_01", "no difference", "wrong"),
    # Lists
    ("q_lists_01", "fruits[0] accesses 'apple'. Python uses 0-based indexing, so the first element is at index 0 and fruits[1] is 'banana'.", "full"),
    ("q_lists_01", "fruits[0], because indexing starts at 0 so [1] is banana", "full"),
    ("q_lists_01", "use fruits[0]; python is zero-based", "full"),
    ("q_lists_01", "fruits[0] because Python counts from zero", "full"),
    ("q_lists_01", "fruits[0]", "partial"),
    ("q_lists_01", "fruits[1] is apple", "wrong"),
    ("q_lists_01", "the second item is apple", "wrong"),
    ("q_lists_01", "fruits[1]", "wrong"),
    # For loops
    ("q_loops_01", "[1, 2, 3, 4]. The stop value 5 is exclusive ('up to but not including 5').", "full"),
    ("q_loops_01", "1, 2, 3, 4 because the stop value is exclusive", "full"),
    ("q_loops_01", "[1, 2, 3, 4], 5 is not included", "full"),
    ("q_loops_01", "1,2,3,4", "partial"),
    ("q_loops_01", "1, 2, 3, 4, 5", "wrong"),
    ("q_loops_01", "includes 5", "wrong"),
    ("q_loops_01", "5 is included", "wrong"),
    # While loops
    ("q_while_01", "An infinite loop occurs when the condition never evaluates to False. To prevent it, you must update/increment the loop variable inside the body so the condition eventually terminates.", "full"),
    ("q_while_01", "if the condition never becomes false because you never update the counter", "full"),
    ("q_while_01", "the condition stays true forever unless you change the variable", "full"),
    ("q_while_01", "you must increment the loop variable inside the loop so it eventually terminates", "partial"),
    ("q_while_01", "you forgot to increment the counter", "full"),
    ("q_while_01", "break only", "wrong"),
    ("q_while_01", "you can't prevent it", "wrong"),
    # Functions
    ("q_fn_01", "print() displays text on the screen for humans to see and returns None. 'return' sends the computed value back to the caller so it can be stored in a variable or used in further calculations.", "full"),
    ("q_fn_01", "print only shows text on screen, return sends the value back to the caller", "full"),
    ("q_fn_01", "print displays it but gives back None; return lets you store the value", "full"),
    ("q_fn_01", "return passes a value back so you can use it later, print just shows it", "full"),
    ("q_fn_01", "print shows text; return gives a value back", "full"),
    ("q_fn_01", "return sends the value back to the caller", "partial"),
    ("q_fn_01", "print gives a value back", "wrong"),
    ("q_fn_01", "print display", "wrong"),
    ("q_fn_01", "print return", "wrong"),
    ("q_fn_01", "same thing", "wrong"),
    ("q_fn_01", "print returns the value", "wrong"),
]


@pytest.mark.parametrize("qid,answer,expected", MAIN_CASES)
def test_main_question_grading(qid, answer, expected):
    result = QS.evaluate_main_question(QS.questions[qid], answer)
    assert status(result) == expected, (
        f"{qid}: expected {expected}, got {status(result)} "
        f"(score={result.score}, feedback={result.feedback})"
    )


FOLLOWUP_CASES = [
    ("q_var_01", "8", True),
    ("q_var_01", "count becomes 8", True),
    ("q_var_01", "6", False),
    ("q_var_01", "18", False),
    ("q_var_02", "score2 is 50", True),
    ("q_var_02", "100", False),
    ("q_var_02", "score2 is 100", False),
    ("q_var_03", "temp = first\nfirst = second\nsecond = temp", True),
    ("q_var_03", "first, second = second, first", True),
    ("q_var_03", "save first in temp, copy second into first, then put temp into second", True),
    ("q_var_03", "first = second; second = first", False),
    ("q_var_03", "first = second", False),
    ("q_var_03", "temp=first first=second second=temp", True),
    ("q_var_03", "temp = first first = second second = temp", True),
    ("q_var_03", "b=first first=second second=b", True),
    ("q_var_03", "first=second second=first", False),
    # A transfer answer must contain all three swap steps, not one keyword.
    ("q_var_03", "first into temp", False),
    ("q_var_03", "copy second", False),
    ("q_var_03", "save first in temp, copy second into first", False),
    ("q_var_03", "temp holds first, first holds second, second holds temp", True),
    ("q_var_03", "temp = first", False),
    ("q_types_01", "HelloWorld", True),
    ("q_types_01", "it glues them into HelloWorld", True),
    ("q_types_01", "Hello World", False),
    ("q_ops_01", "4", True),
    ("q_ops_01", "4.5", False),
    ("q_ops_01", "4.0", False),
    ("q_cond_01", "only B", True),
    ("q_cond_01", "B", True),
    ("q_cond_01", "B and C", False),
    ("q_lists_01", "fruits[-1]", True),
    ("q_lists_01", "fruits[2]", False),
    ("q_loops_01", "3 times", True),
    ("q_loops_01", "4 times", False),
    ("q_while_01", "count += 1", True),
    ("q_while_01", "print(count)", False),
    ("q_fn_01", "x will be None", True),
    ("q_fn_01", "x will be 5", False),
]


@pytest.mark.parametrize("qid,answer,expected", FOLLOWUP_CASES)
def test_followup_grading(qid, answer, expected):
    result = QS.evaluate_followup(QS.questions[qid], answer)
    assert result.is_correct is expected, (
        f"{qid} follow-up: expected {expected}, got {result.is_correct} ({result.feedback})"
    )


SCAFFOLD_CASES = [
    ("q_var_01", 1, "6", True), ("q_var_01", 1, "16", False),
    ("q_var_01", 2, "x", True), ("q_var_01", 2, "y", False),
    ("q_var_02", 1, "10", True), ("q_var_02", 1, "20", False),
    ("q_var_02", 2, "no", True), ("q_var_02", 2, "it will not change", True),
    ("q_var_03", 1, "temp = x", True), ("q_var_03", 1, "x = temp", False),
    ("q_var_03", 2, "x = y", True), ("q_var_03", 2, "y = x", False),
    ("q_var_03", 3, "y = temp", True), ("q_var_03", 3, "temp = y", False),
    ("q_types_01", 1, "str", True), ("q_types_01", 1, "int", False),
    ("q_types_01", 2, "glue", True), ("q_types_01", 2, "add", False),
    ("q_types_02", 1, "int", True), ("q_types_02", 1, "str", False),
    ("q_ops_01", 1, "/", True), ("q_ops_01", 1, "//", False),
    ("q_ops_01", 2, "chops it off", True), ("q_ops_01", 2, "keeps it", False),
    ("q_cond_01", 1, "no", True), ("q_cond_01", 1, "yes", False),
    ("q_lists_01", 1, "0", True), ("q_lists_01", 1, "10", False),
    ("q_loops_01", 1, "no", True), ("q_loops_01", 1, "yes", False),
    ("q_while_01", 1, "no", True), ("q_while_01", 1, "yes", False),
    ("q_fn_01", 1, "no", True), ("q_fn_01", 1, "yes", False),
]


@pytest.mark.parametrize("qid,step_number,answer,expected", SCAFFOLD_CASES)
def test_scaffold_grading(qid, step_number, answer, expected):
    step = next(s for s in QS.questions[qid].scaffold_steps if s.step_number == step_number)
    result = QS.evaluate_scaffold_step(step, answer)
    assert result.is_correct is expected, (
        f"{qid} step {step_number}: expected {expected} for {answer!r}, got {result.is_correct}"
    )


@pytest.mark.parametrize("qid", list(QS.questions))
def test_canonical_main_answer_earns_full_credit(qid):
    question = QS.questions[qid]
    result = QS.evaluate_main_question(question, question.canonical_answer)
    assert result.is_correct and result.score == 1.0, (
        f"Canonical answer rejected for {qid}: {result.feedback}"
    )


@pytest.mark.parametrize("qid", [qid for qid, q in QS.questions.items() if q.followup])
def test_canonical_followup_answer_is_accepted(qid):
    question = QS.questions[qid]
    result = QS.evaluate_followup(question, question.followup.canonical_answer)
    assert result.is_correct, f"Canonical follow-up rejected for {qid}: {result.feedback}"


@pytest.mark.parametrize("qid", list(QS.questions))
def test_scaffold_expected_answers_are_accepted(qid):
    for step in QS.questions[qid].scaffold_steps:
        assert QS.evaluate_scaffold_step(step, step.expected_answer).is_correct, (
            f"Scaffold expected answer rejected for {qid} step {step.step_number}"
        )


MISCONCEPTION_CASES = [
    ("q_var_01", "no solution", "confuse_assign_equals"),
    ("q_var_02", "b is 20 because a changed", "variable_permanent_link"),
    ("q_var_03", "x = y; y = x", "swap_data_loss"),
    ("q_types_01", "10", "string_number_conflation"),
    ("q_ops_01", "7/2 is 3 and 7//2 is 3.5", "division_types_confusion"),
    ("q_cond_01", "same thing", "multiple_if_vs_elif"),
    ("q_lists_01", "fruits[1] is apple", "one_based_indexing_error"),
    ("q_loops_01", "includes 5", "range_inclusive_stop"),
    ("q_while_01", "break only", "missing_loop_increment"),
    ("q_fn_01", "print returns the value", "print_vs_return_conflation"),
]


@pytest.mark.parametrize("qid,answer,expected_id", MISCONCEPTION_CASES)
def test_detected_misconception_ids(qid, answer, expected_id):
    result = QS.evaluate_main_question(QS.questions[qid], answer)
    assert result.is_correct is False
    assert result.detected_misconceptions == [expected_id]
