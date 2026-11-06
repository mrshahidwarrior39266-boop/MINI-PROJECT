"""
Response Evaluator Service:
Analyzes the student's natural language or code response against
ground truth concepts, rubrics, and the catalog of known misconceptions.
"""
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from app.models.concept import Concept, Misconception


class EvaluationResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    is_correct: bool
    detected_misconceptions: List[str] = Field(default_factory=list)
    feedback: str
    remediation_hint: str = ""


class HeuristicEvaluator:
    """
    Rubric-based evaluation engine for Milestone 1/2.
    Detects conceptual understanding and specific cognitive bugs
    without requiring external cloud API keys, with full LLM extensibility.
    """

    @classmethod
    def evaluate(cls, concept: Concept, question: str, user_answer: str) -> EvaluationResult:
        ans = user_answer.strip().lower()
        
        # 1. Concept: py.variables
        if concept.id == "py.variables":
            return cls._eval_variables(concept, question, ans)

        # 2. Concept: py.data_types
        elif concept.id == "py.data_types":
            return cls._eval_data_types(concept, question, ans)

        # 3. Concept: py.operators_expressions
        elif concept.id == "py.operators_expressions":
            return cls._eval_operators(concept, question, ans)

        # Generic fallback
        if len(ans) < 3:
            return EvaluationResult(
                score=0.1,
                is_correct=False,
                feedback="Your response seems too brief. Try to explain what Python is doing step-by-step."
            )
        return EvaluationResult(
            score=0.8,
            is_correct=True,
            feedback="Good effort! You demonstrated basic comprehension of the topic."
        )

    @classmethod
    def _eval_variables(cls, concept: Concept, question: str, ans: str) -> EvaluationResult:
        # Check for algebra equality misconception (e.g. "x = x + 1")
        if any(term in ans for term in ["impossible", "no solution", "algebra", "cannot equal", "math error", "can't be equal"]):
            return EvaluationResult(
                score=0.25,
                is_correct=False,
                detected_misconceptions=["confuse_assign_equals"],
                feedback="You treated '=' as an algebraic equality equation. In Python, '=' does not mean 'equals'!",
                remediation_hint="Think of '=' as an arrow (<-). Python calculates the right side first (x + 1), then stores the result back into the variable on the left."
            )

        # Check for transfer question evaluation (score1 = 50, score2 = 50)
        if "score1" in question.lower() or "score2" in question.lower():
            if "100" in ans:
                return EvaluationResult(
                    score=0.0,
                    is_correct=False,
                    detected_misconceptions=["variable_permanent_link"],
                    feedback="Incorrect. score2 is 50, NOT 100. score2 got a snapshot of score1 when it was 50.",
                    remediation_hint="Changing score1 to 100 later has no effect on score2."
                )
            if "50" in ans:
                return EvaluationResult(
                    score=1.0,
                    is_correct=True,
                    feedback="Spot on! score2 is 50 because assignment captures the value at that moment in time. You fixed the misconception!"
                )
        if ans == "20" or "permanent" in ans or "linked" in ans or "update automatically" in ans or "both change" in ans:
            return EvaluationResult(
                score=0.0,
                is_correct=False,
                detected_misconceptions=["variable_permanent_link"],
                feedback="Incorrect. The value of 'b' is 10, NOT 20. Changing 'a' later does not change 'b'.",
                remediation_hint="Variables are one-time snapshots, not live links. When 'b = a' executed, 'a' was 10, so 'b' got 10. Reassigning 'a' to 20 later leaves 'b' completely untouched."
            )

        # Check for correct answer 10
        if "10" in ans and "20" not in ans:
            return EvaluationResult(
                score=1.0,
                is_correct=True,
                feedback="Correct! b is 10. Assignment copies the value at that moment; changing 'a' later has no effect on 'b'."
            )

        # Positive understanding checks
        key_terms = ["assign", "bind", "store", "memory", "label", "points", "value", "reference", "temp", "copy"]
        matched_terms = [t for t in key_terms if t in ans]

        if "swap" in question.lower() or "temp" in question.lower():
            if ("temp" in ans or "a, b = b, a" in ans) and ("=" in ans or ";" in ans or "," in ans):
                return EvaluationResult(
                    score=1.0,
                    is_correct=True,
                    feedback="Spot on! You correctly preserved the values during assignment."
                )

        # Strict check: Require real domain terms, never give points merely for string length
        if len(matched_terms) >= 2 or ("5" in ans and ("reference" in ans or "copy" in ans or "box" in ans or "bind" in ans or "value" in ans)):
            return EvaluationResult(
                score=1.0,
                is_correct=True,
                feedback="Excellent! You clearly understand variable assignment and memory references."
            )
        elif len(matched_terms) == 1:
            return EvaluationResult(
                score=0.6,
                is_correct=True,
                feedback="Partially correct. You mentioned the right concept, but try to explain the steps more thoroughly."
            )
        else:
            return EvaluationResult(
                score=0.0,
                is_correct=False,
                feedback="Your answer does not address the question. Explain what Python is doing with variables, assignment, or memory."
            )

    @classmethod
    def _eval_data_types(cls, concept: Concept, question: str, ans: str) -> EvaluationResult:
        # Check string number conflation: expecting "5" + "5" to be 10
        if "10" in ans and "55" not in ans and ("quote" not in ans):
            return EvaluationResult(
                score=0.25,
                is_correct=False,
                detected_misconceptions=["string_number_conflation"],
                feedback="You calculated 10, but notice the quotation marks: '5' + '5' are strings (text)!",
                remediation_hint="When text is added with '+', Python glues the characters together (concatenation), resulting in '55', not 10."
            )

        if "55" in ans or "string" in ans or "str" in ans or "concat" in ans:
            return EvaluationResult(
                score=1.0,
                is_correct=True,
                feedback="Great job! You recognize that quotes indicate text strings, resulting in concatenation ('55')."
            )

        return EvaluationResult(
            score=0.8,
            is_correct=True,
            feedback="Good answer! You accurately identified the data types."
        )

    @classmethod
    def _eval_operators(cls, concept: Concept, question: str, ans: str) -> EvaluationResult:
        if "division" in question.lower():
            if "3.5" in ans and "3" in ans:
                return EvaluationResult(
                    score=1.0,
                    is_correct=True,
                    feedback="Correct! In Python 3, '/' gives 3.5 (float) while '//' performs floor division returning 3."
                )
        return EvaluationResult(
            score=0.75,
            is_correct=True,
            feedback="Accurate analysis of operators."
        )
