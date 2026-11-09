"""
Universal Question and Assessment Service:
Provides structured educational questions, rubric evaluation, step-by-step explanations,
and automatic follow-up transfer questions across the entire curriculum database.

Grading notes:
- Keyword matching is boundary aware, so "4" no longer matches "4.5" and "b" no longer
  matches "because".
- A keyword that appears in a negated phrase ("it is not 10") is not counted as evidence.
- Known mistakes are checked before positive keywords, so a confident wrong answer cannot
  pass just by sprinkling in a correct-sounding word.
- Code answers are executed and verified by state, not by matching variable names.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set

from pydantic import BaseModel, Field

from app.models.question import CurriculumQuestion, FollowupQuestion, QuestionMistakePattern
from app.services.logic_verifier import run_symbolic_code_evaluation, check_swap_goal

_APOSTROPHE_MAP = str.maketrans({
    "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
})

_NEGATORS = {
    "not", "no", "never", "cannot", "can't", "cant", "without", "nor",
    "isn't", "isnt", "aren't", "arent", "doesn't", "doesnt",
    "don't", "dont", "didn't", "didnt", "won't", "wont",
}
_PUNCTUATION = set("=,+*/\\()[]{}")


def normalize_code_string(text: str) -> str:
    """Normalizes whitespace around operators so 'temp=first' and 'temp = first' match identically."""
    norm = re.sub(r"\s*([=;,+*/\\()\[\]])\s*", r"\1", text.lower())
    return re.sub(r"\s+", " ", norm).strip()


def _plain(text: str) -> str:
    """Lowercase, normalize quotes, treat hyphens as spaces, collapse whitespace."""
    value = text.translate(_APOSTROPHE_MAP).lower().replace("-", " ")
    return re.sub(r"\s+", " ", value).strip()


def _compact(text: str) -> str:
    """
    Normalize code-shaped text: ignore spaces around punctuation, but keep a
    space between statements so one keyword cannot bleed into the next statement.
    """
    value = text.translate(_APOSTROPHE_MAP).lower().replace("-", " ")
    value = re.sub(r"\s*([=;,+*/\\()\[\]])\s*", r"\1", value)
    return re.sub(r"\s+", " ", value).strip()


def _is_numeric_keyword(keyword: str) -> bool:
    return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", keyword))


def _keyword_pattern(keyword: str) -> Tuple[str, str]:
    """
    Build a boundary-aware regex pattern for a keyword.
    Returns (pattern, haystack_kind) where haystack_kind is "plain" or "compact".
    """
    kw_plain = _plain(keyword)
    kw_compact = _compact(keyword)

    if _is_numeric_keyword(kw_plain):
        return rf"(?<![\d.]){re.escape(kw_plain)}(?![\d.])", "plain"

    # Pure language keywords (letters/apostrophes/spaces) match against the readable text.
    if re.fullmatch(r"[a-z]+(?:'[a-z]+)?(?:\s+[a-z]+(?:'[a-z]+)?)*", kw_plain):
        body = r"\s+".join(re.escape(word) for word in kw_plain.split())
        prefix = r"(?<![a-z])"
        suffix = r"(?![a-z])" if len(kw_plain) <= 3 else ""
        return prefix + body + suffix, "plain"

    # Code-shaped keywords match without whitespace, but still respect identifier edges.
    prefix = r"(?<![A-Za-z0-9_])" if kw_compact[:1].isalnum() or kw_compact[:1] == "_" else ""
    suffix = r"(?![A-Za-z0-9_])" if kw_compact[-1:].isalnum() or kw_compact[-1:] == "_" else ""
    return prefix + re.escape(kw_compact) + suffix, "compact"


def _keyword_hit(keyword: str, plain: str, compact: str) -> bool:
    pattern, haystack = _keyword_pattern(keyword)
    text = plain if haystack == "plain" else compact
    return re.search(pattern, text) is not None


def _negated_at(plain: str, start: int, window: int = 32, lookback_words: int = 3) -> bool:
    """True when a match is preceded by a negator such as 'not', 'never', or "doesn't"."""
    prefix = plain[max(0, start - window):start]
    words = re.findall(r"[a-z']+", prefix)[-lookback_words:]
    return any(word in _NEGATORS or word.endswith("n't") for word in words)


def _trigger_pattern(trigger: str) -> str:
    """A tolerant trigger pattern: spaces around punctuation are optional and word edges are respected."""
    phrase = _plain(trigger)
    if _is_numeric_keyword(phrase):
        return rf"(?<![\d.]){re.escape(phrase)}(?![\d.])"

    pieces = []
    for char in phrase:
        if char == " ":
            pieces.append(r"\s*")
        elif char in _PUNCTUATION:
            pieces.append(r"\s*" + re.escape(char) + r"\s*")
        else:
            pieces.append(re.escape(char))

    pattern = "".join(pieces)
    if phrase[:1].isalpha():
        pattern = r"(?<![A-Za-z])" + pattern
    if phrase[-1:].isalpha():
        pattern = pattern + r"(?![A-Za-z])"
    return pattern


def _mistake_matches(mistake: QuestionMistakePattern, plain: str, compact: str) -> bool:
    """True when a mistake pattern appears outside a negated phrase."""
    for regex in mistake.regex_triggers:
        if re.search(regex, plain, flags=re.IGNORECASE):
            return True

    for trigger in mistake.triggers:
        positions = [m.start() for m in re.finditer(_trigger_pattern(trigger), plain)]
        if positions:
            if any(not _negated_at(plain, pos) for pos in positions):
                return True
            continue

        # Fall back to punctuation-insensitive matching for code-shaped triggers.
        trigger_compact = _compact(trigger)
        if trigger_compact and trigger_compact in compact:
            return True

    return False


def _first_mistake(question: CurriculumQuestion, plain: str, compact: str) -> Optional[QuestionMistakePattern]:
    for mistake in question.common_mistakes:
        if _mistake_matches(mistake, plain, compact):
            return mistake
    return None


def _first_followup_mistake(followup: FollowupQuestion, plain: str, compact: str) -> Optional[QuestionMistakePattern]:
    for mistake in followup.common_mistakes:
        if _mistake_matches(mistake, plain, compact):
            return mistake
    return None


def _positive_hits(question: CurriculumQuestion, plain: str, compact: str) -> List[str]:
    return [kw for kw in question.rubric_keywords if _keyword_hit(kw, plain, compact)]


def _is_substantive(plain: str) -> bool:
    """Require at least a short sentence of explanation, not a stuffed pair of buzzwords."""
    words = re.findall(r"[a-z0-9]+", plain)
    if len(words) >= 3:
        return True
    if "=" in plain and len(words) >= 2:
        return True
    # A short code answer like int(age) is substantive even with only two tokens.
    return bool(re.search(r"[()\[\]]", plain)) and len(words) >= 2


def _groups_satisfied(groups: List[List[str]], plain: str, compact: str) -> bool:
    """Every idea group must be represented by at least one of its synonyms."""
    return all(
        any(_keyword_hit(keyword, plain, compact) for keyword in group)
        for group in groups
    )


def _required_groups_satisfied(question: CurriculumQuestion, plain: str, compact: str) -> bool:
    return _groups_satisfied(question.required_keyword_groups, plain, compact)


def _evidence_sufficient(hits: List[str], plain: str, required: int = 1) -> bool:
    if len(hits) >= 2:
        return _is_substantive(plain)
    if required >= 2:
        return False
    return len(hits) == 1 and _is_substantive(plain)


def _swap_steps_present(compact: str) -> bool:
    """Recognise a complete textual description of the three-step swap."""
    has_temp = "temp=x" in compact or "temporary=x" in compact
    return (has_temp and "x=y" in compact and "y=temp" in compact) or "x,y=y,x" in compact


_SWAP_PROSE_HINT = re.compile(
    r"\b(?:save|copy|put|store|move|assign|set)\b.*\b(?:in|into|to|inside)\b",
    re.IGNORECASE,
)


def _looks_like_swap_steps(text: str) -> bool:
    """True when prose describes concrete save/copy/put steps worth executing."""
    return bool(_SWAP_PROSE_HINT.search(text))


def _swap_code_failure_known(message: str) -> bool:
    return message != "NO_CODE"


def _format_swap_failure(message: str) -> str:
    if message.startswith("Data lost"):
        return "Logical flaw: You overwrote one variable before saving its value into temporary storage!"
    if message.startswith("NameError"):
        return f"Your code used a name before giving it a value. {message}"
    return f"Your code did not swap the values. {message}"


class UniversalEvaluationResult(BaseModel):
    is_correct: bool
    score: float = Field(..., ge=0.0, le=1.0)
    diagnosis: Optional[str] = None
    canonical_answer: str
    explanation: str
    feedback: str
    detected_misconceptions: List[str] = Field(default_factory=list)
    has_followup: bool = False
    followup_question: Optional[FollowupQuestion] = None


class QuestionService:
    def __init__(self, questions_file: Optional[Path] = None):
        self.questions: Dict[str, CurriculumQuestion] = {}
        self.concept_questions: Dict[str, List[CurriculumQuestion]] = {}

        if questions_file and questions_file.exists():
            self.load_from_json(questions_file)

    def load_from_json(self, file_path: Path) -> None:
        """Load questions from JSON database."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Question data must be a JSON list.")

        for item in data:
            q = CurriculumQuestion(**item)
            if q.id in self.questions:
                raise ValueError(f"Duplicate question id: {q.id}")
            self.questions[q.id] = q
            if q.concept_id not in self.concept_questions:
                self.concept_questions[q.concept_id] = []
            self.concept_questions[q.concept_id].append(q)

    def get_questions_for_concept(self, concept_id: str) -> List[CurriculumQuestion]:
        """Fetch all questions for a specific concept."""
        return self.concept_questions.get(concept_id, [])

    def validate(
        self,
        concept_ids: Optional[Set[str]] = None,
        misconception_catalog: Optional[Set[Tuple[str, str]]] = None,
    ) -> None:
        """
        Fail fast on malformed curriculum data instead of crashing mid-session.

        Every question must have a usable main rubric, a transfer follow-up,
        and guided scaffolding. When a concept catalog is supplied, every
        question must belong to a real concept and every referenced
        misconception must exist in that concept's catalog.
        """
        if not self.questions:
            raise ValueError(
                "No questions were loaded. Check app/data/curriculum_questions.json."
            )

        if concept_ids is not None:
            missing = sorted(set(concept_ids) - set(self.concept_questions))
            if missing:
                raise ValueError(
                    "No questions found for concept(s): " + ", ".join(missing)
                )
            orphans = sorted(set(self.concept_questions) - set(concept_ids))
            if orphans:
                raise ValueError(
                    "Questions reference unknown concept(s): " + ", ".join(orphans)
                )

        for q in self.questions.values():
            for label, value in (
                ("prompt", q.prompt),
                ("canonical answer", q.canonical_answer),
                ("explanation", q.explanation),
            ):
                if not value.strip():
                    raise ValueError(f"Question {q.id} has an empty {label}.")

            if not q.rubric_keywords and not q.required_keyword_groups:
                raise ValueError(f"Question {q.id} has no grading rubric.")
            if any(not group for group in q.required_keyword_groups):
                raise ValueError(f"Question {q.id} has an empty keyword group.")

            if q.followup is None:
                raise ValueError(f"Question {q.id} has no transfer follow-up.")
            if not q.followup.prompt.strip() or not q.followup.canonical_answer.strip():
                raise ValueError(f"Question {q.id} has an incomplete follow-up.")
            if not q.followup.rubric_keywords and not q.followup.required_keyword_groups:
                raise ValueError(f"Question {q.id} follow-up has no grading rubric.")
            if any(not group for group in q.followup.required_keyword_groups):
                raise ValueError(f"Question {q.id} follow-up has an empty keyword group.")

            if not q.scaffold_steps:
                raise ValueError(f"Question {q.id} has no guided scaffolding steps.")
            for step in q.scaffold_steps:
                if not step.prompt.strip() or not step.expected_answer.strip():
                    raise ValueError(
                        f"Question {q.id} step {step.step_number} is incomplete."
                    )

            for mistake in q.common_mistakes:
                if not mistake.triggers and not mistake.regex_triggers:
                    raise ValueError(
                        f"Question {q.id} has a misconception pattern with no triggers."
                    )
                if (
                    misconception_catalog is not None
                    and mistake.misconception_id
                    and (q.concept_id, mistake.misconception_id) not in misconception_catalog
                ):
                    raise ValueError(
                        f"Question {q.id} references unknown misconception "
                        f"'{mistake.misconception_id}' for {q.concept_id}."
                    )

    # ------------------------------------------------------------------
    # Main question evaluation
    # ------------------------------------------------------------------
    def evaluate_main_question(
        self,
        question: CurriculumQuestion,
        student_answer: str
    ) -> UniversalEvaluationResult:
        """
        Universally evaluates an answer for ANY question in the database:
        1. Executes code answers when the question asks for a swap (logic over phrasing).
        2. Checks known misconception triggers (negation aware).
        3. Evaluates rubric keywords with word/number boundaries.
        4. Returns full step-by-step explanation and attaches the transfer follow-up.
        """
        ans = student_answer.strip()
        plain = _plain(ans)
        compact = _compact(ans)

        if not ans:
            return self._wrong(
                question,
                diagnosis="You didn't enter an answer.",
                feedback="Please try explaining the mechanism in your own words."
            )

        is_swap = "swap" in question.prompt.lower()
        if is_swap and ("=" in ans or _looks_like_swap_steps(ans)):
            valid, message = run_symbolic_code_evaluation(
                code_str=ans,
                setup_env={"x": 100, "y": 200},
                goal_check=check_swap_goal("x", "y")
            )
            if valid:
                return UniversalEvaluationResult(
                    is_correct=True,
                    score=1.0,
                    canonical_answer=question.canonical_answer,
                    explanation=question.explanation,
                    feedback="Spot on! The computer executed your logic in memory and verified the values swapped perfectly!"
                )
            if _swap_code_failure_known(message):
                if message.startswith("Data lost"):
                    misconception_id = "swap_data_loss"
                elif message.startswith("NameError"):
                    misconception_id = "undefined_variable_in_swap"
                else:
                    misconception_id = None
                return self._wrong(
                    question,
                    diagnosis=_format_swap_failure(message),
                    feedback=_format_swap_failure(message),
                    misconception_id=misconception_id
                )

        if is_swap and _swap_steps_present(compact):
            return UniversalEvaluationResult(
                is_correct=True,
                score=1.0,
                canonical_answer=question.canonical_answer,
                explanation=question.explanation,
                feedback="Spot on! You correctly preserved the values using temporary storage."
            )

        mistake = _first_mistake(question, plain, compact)
        if mistake:
            return self._wrong(
                question,
                diagnosis=mistake.diagnosis,
                feedback=f"Incorrect. {mistake.diagnosis}",
                misconception_id=mistake.misconception_id
            )

        hits = _positive_hits(question, plain, compact)
        groups_ok = _required_groups_satisfied(question, plain, compact)
        if groups_ok and _evidence_sufficient(hits, plain, question.min_keyword_hits):
            return UniversalEvaluationResult(
                is_correct=True,
                score=1.0,
                canonical_answer=question.canonical_answer,
                explanation=question.explanation,
                feedback="Excellent! You gave an accurate and conceptually sound answer."
            )

        if hits:
            if not groups_ok:
                diagnosis = (
                    "You covered part of the mechanism, but this question asks for the full picture. "
                    "Explain the missing part too."
                )
            else:
                diagnosis = (
                    f"You identified part of the idea ('{hits[0]}'), but the answer is too brief "
                    "to show the full mechanism. Explain what happens step by step."
                )
            return UniversalEvaluationResult(
                is_correct=False,
                score=0.5,
                diagnosis=diagnosis,
                canonical_answer=question.canonical_answer,
                explanation=question.explanation,
                feedback="Half credit: you found the right idea, but the explanation needs more detail.",
                has_followup=question.followup is not None,
                followup_question=question.followup
            )

        return self._wrong(
            question,
            diagnosis="Your answer did not match the expected mechanism.",
            feedback="Incorrect. Let's inspect how this works step-by-step."
        )

    # ------------------------------------------------------------------
    # Follow-up transfer question evaluation
    # ------------------------------------------------------------------
    def evaluate_followup(
        self,
        question: CurriculumQuestion,
        student_answer: str
    ) -> UniversalEvaluationResult:
        """Evaluates the transfer follow-up question with boundary-aware matching."""
        if not question.followup:
            return UniversalEvaluationResult(
                is_correct=True,
                score=1.0,
                canonical_answer="",
                explanation="",
                feedback="Correct!"
            )

        followup = question.followup
        ans = student_answer.strip()
        plain = _plain(ans)
        compact = _compact(ans)

        if not ans:
            return self._followup_wrong(followup, "You didn't enter an answer.")

        if (
            ("swap" in question.prompt.lower() or "swap" in followup.prompt.lower())
            and ("=" in ans or _looks_like_swap_steps(ans))
        ):
            valid, message = run_symbolic_code_evaluation(
                code_str=ans,
                setup_env={"first": 100, "second": 200},
                goal_check=check_swap_goal("first", "second")
            )
            if valid:
                return UniversalEvaluationResult(
                    is_correct=True,
                    score=1.0,
                    canonical_answer=followup.canonical_answer,
                    explanation="You successfully executed the swap logic in memory!",
                    feedback="Spot on! The computer verified your logic by running it: 'first' and 'second' swapped cleanly!"
                )
            if _swap_code_failure_known(message):
                return self._followup_wrong(followup, _format_swap_failure(message))

        mistake = _first_followup_mistake(followup, plain, compact)
        if mistake:
            return self._followup_wrong(followup, mistake.diagnosis)

        hits = [
            kw for kw in followup.rubric_keywords
            if _keyword_hit(kw, plain, compact)
        ]
        if followup.required_keyword_groups:
            groups_ok = _groups_satisfied(
                followup.required_keyword_groups, plain, compact
            )
            if (
                groups_ok
                and len(hits) >= followup.min_keyword_hits
                and _is_substantive(plain)
            ):
                return UniversalEvaluationResult(
                    is_correct=True,
                    score=1.0,
                    canonical_answer=followup.canonical_answer,
                    explanation="You successfully applied the concept to a new scenario!",
                    feedback="Great job! You mastered this follow-up challenge."
                )
            if hits:
                return self._followup_wrong(
                    followup,
                    "You covered part of the transfer challenge, but it needs all of the required steps."
                )
        elif hits:
            return UniversalEvaluationResult(
                is_correct=True,
                score=1.0,
                canonical_answer=followup.canonical_answer,
                explanation="You successfully applied the concept to a new scenario!",
                feedback="Great job! You mastered this follow-up challenge."
            )

        canonical = followup.canonical_answer
        if _phrase_or_code_match(canonical, plain, compact):
            return UniversalEvaluationResult(
                is_correct=True,
                score=1.0,
                canonical_answer=canonical,
                explanation="You successfully applied the concept to a new scenario!",
                feedback="Great job! You mastered this follow-up challenge."
            )

        return self._followup_wrong(
            followup,
            f"Not quite. Expected: {followup.canonical_answer}"
        )

    # ------------------------------------------------------------------
    # Guided scaffolding micro-step evaluation
    # ------------------------------------------------------------------
    def evaluate_scaffold_step(
        self,
        step: Any,
        student_answer: str
    ) -> UniversalEvaluationResult:
        """Evaluates an atomic guided scaffolding micro-step."""
        ans = student_answer.strip()
        plain = _plain(ans)
        compact = _compact(ans)
        expected_plain = _plain(step.expected_answer)
        expected_compact = _compact(step.expected_answer)

        # Exact match is always accepted.
        if compact and compact == expected_compact:
            return self._scaffold_right(step)

        # Single-character answers (like "/") may only be matched exactly.
        if len(expected_compact) <= 1:
            return self._scaffold_wrong(step)

        if _keyword_hit(step.expected_answer, plain, compact):
            return self._scaffold_right(step)

        if any(_keyword_hit(kw, plain, compact) for kw in step.rubric_keywords):
            return self._scaffold_right(step)

        return self._scaffold_wrong(step)

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------
    def _wrong(
        self,
        question: CurriculumQuestion,
        diagnosis: str,
        feedback: str,
        misconception_id: Optional[str] = None
    ) -> UniversalEvaluationResult:
        return UniversalEvaluationResult(
            is_correct=False,
            score=0.0,
            diagnosis=diagnosis,
            canonical_answer=question.canonical_answer,
            explanation=question.explanation,
            feedback=feedback,
            detected_misconceptions=[misconception_id] if misconception_id else [],
            has_followup=question.followup is not None,
            followup_question=question.followup
        )

    def _followup_wrong(self, followup: FollowupQuestion, diagnosis: str) -> UniversalEvaluationResult:
        return UniversalEvaluationResult(
            is_correct=False,
            score=0.0,
            diagnosis=diagnosis,
            canonical_answer=followup.canonical_answer,
            explanation="Review the reference answer above to see the correct sequence.",
            feedback=diagnosis
        )

    def _scaffold_right(self, step: Any) -> UniversalEvaluationResult:
        return UniversalEvaluationResult(
            is_correct=True,
            score=1.0,
            canonical_answer=step.expected_answer,
            explanation=step.explanation,
            feedback="Correct! That micro-step is complete."
        )

    def _scaffold_wrong(self, step: Any) -> UniversalEvaluationResult:
        return UniversalEvaluationResult(
            is_correct=False,
            score=0.0,
            canonical_answer=step.expected_answer,
            explanation=step.explanation,
            feedback=f"Not quite. Expected: {step.expected_answer}"
        )


def _phrase_or_code_match(canonical: str, plain: str, compact: str) -> bool:
    """Accept the canonical answer when it is textual, or when it is code that was typed compactly."""
    if re.search(r"[=;\[\]()]", canonical):
        canonical_compact = _compact(canonical)
        return bool(canonical_compact) and canonical_compact in compact
    # Textual canonicals still need the same boundaries as rubric keywords:
    # otherwise canonical "4" would accept a student answer of "4.5".
    return _keyword_hit(canonical, plain, compact)
