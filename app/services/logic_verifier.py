"""
Logic-First Execution and AST Verifier:
Executes and verifies student code dynamically in isolated memory environments
to evaluate computational LOGIC, completely independent of variable names,
spacing, formatting, or stylistic variations.
"""
import ast
import re
from typing import Tuple, Dict, Any, List, Optional

# Leading words students use when they describe code in prose.
_LEADING_NOISE = re.compile(
    r"^(?:and|then|next|finally|first|firstly|second|secondly|third|thirdly|"
    r"last|lastly|step\s*\d+|use|using|do|write|type|just|simply|so)\b[\s:,-]*",
    re.IGNORECASE,
)

_ASSIGNMENT = re.compile(
    r"^[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*=\s*[^=].*$"
)
_PLAIN_ASSIGNMENT = re.compile(
    r"^[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*\s*=\s*"
    r"(?:[A-Za-z_]\w*|-?\d+(?:\.\d+)?|['\"][^'\"]*['\"]|"
    r"[A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)$"
)

# Trailing prose students add after the actual code.
_PROSE_TAIL = re.compile(r"\s+(?:and|then|because|so)\s+(.*)$", re.IGNORECASE)
_TRAILING_CONNECTOR = re.compile(
    r"[\s,]+(?:and|then|because|so|which|that)\s*$", re.IGNORECASE
)
_NEGATED_CLAUSE = re.compile(
    r"^(?:don't|do\s+not|never|avoid|instead\s+of|not|no)\b", re.IGNORECASE
)
_NEGATIVE_COMMENT = re.compile(
    r"\s+(?:is|was|would\s+be)\s+(?:the\s+)?(?:wrong|incorrect|a\s+mistake|bad)\b",
    re.IGNORECASE,
)
_POSITIVE_COMMENT = re.compile(
    r"\s+(?:(?:is|was)\s+)?(?:correct|right|first|the\s+first\s+step)\b.*$",
    re.IGNORECASE,
)

# Prose descriptions of assignment, e.g. "save x in temp" or "copy y into x".
_PROSE_ASSIGNMENT = re.compile(
    r"\b(?:save|copy|put|store|move|assign)\s+"
    r"(?:the\s+)?(?:value\s+of\s+)?"
    r"['\"]?([A-Za-z_]\w*)['\"]?(?:'s\s+value)?\s+"
    r"(?:in|into|to|inside)\s+"
    r"(?!(?:a|an)\b)(?:(?:the\s+)?variable\s+)?"
    r"['\"]?([A-Za-z_]\w*)['\"]?",
    re.IGNORECASE,
)
_SET_ASSIGNMENT = re.compile(
    r"\bset\s+['\"]?([A-Za-z_]\w*)['\"]?\s+to\s+['\"]?([A-Za-z_]\w*)['\"]?",
    re.IGNORECASE,
)


def _clean_clause(clause: str) -> str:
    """
    Drop trailing explanation and punctuation from an executable clause.

    Examples:
        "y=b and that swaps them" -> "y=b"
        "x = y, then"            -> "x = y"
        "temp = x is correct"    -> "temp = x"
        "x = y is wrong"         -> "" (a counter-example, not a step)
        "y = temp."             -> "y = temp"
    """
    clause = clause.strip()
    if _NEGATIVE_COMMENT.search(clause):
        return ""
    match = _PROSE_TAIL.search(clause)
    if match and "=" not in match.group(1):
        clause = clause[:match.start()]
    clause = _TRAILING_CONNECTOR.sub("", clause)
    clause = clause.strip().strip(".,!?;: ")
    # Do not mistake a plain assignment such as "temp = first" for the
    # commentary phrase "..., first". Only strip a commentary word when the
    # clause is not already a complete, simple assignment.
    if not _PLAIN_ASSIGNMENT.match(clause):
        positive = _POSITIVE_COMMENT.search(clause)
        if positive:
            clause = clause[:positive.start()]
    return clause.strip().strip(".,!?;: ")


def _normalize_prose_assignments(text: str) -> str:
    """
    Turn action descriptions into assignments so prose and code can be graded
    by execution together.

    "save x in temp"       -> "temp = x"
    "copy y into x"        -> "x = y"
    "put temp into y"      -> "y = temp"
    "assign x to temp"     -> "temp = x"
    "set temp to x"        -> "temp = x"
    """
    text = _PROSE_ASSIGNMENT.sub(r"\2 = \1", text)
    return _SET_ASSIGNMENT.sub(r"\1 = \2", text)


def _split_run_together_assignments(text: str) -> str:
    """
    Turn space-separated assignments into lines.

    "b=x x=y y=b" -> "b=x\nx=y\ny=b"

    A boundary is only accepted when the text before it is already a complete
    assignment. That keeps negated prose such as "don't do x = y" together so
    the negation check can reject the whole clause instead of executing the
    counter-example. Tuple unpacking such as "x, y = y, x" stays intact.
    """
    pieces: List[str] = []
    last = 0
    for match in re.finditer(r"\s+(?=[A-Za-z_]\w*\s*=(?!=))", text):
        prefix = text[last:match.start()]
        if _PLAIN_ASSIGNMENT.match(_clean_clause(prefix.strip())):
            pieces.append(prefix)
            last = match.end()
    pieces.append(text[last:])
    return "\n".join(piece for piece in pieces if piece.strip())


def _is_assignment(statement: str) -> bool:
    """True when a clause looks like a plain Python assignment (not a comparison)."""
    return bool(_ASSIGNMENT.match(statement.strip()))


def _split_alternatives(text: str) -> List[str]:
    """
    Split an answer into independent solution blocks.

    The canonical swap answer shows two valid solutions:
        temp = x; x = y; y = temp
        (or in Python: x, y = y, x)
    Running both sequentially would swap twice and look wrong, so each
    alternative must be verified on its own.
    """
    inline_blocks = re.split(
        r"\s+or\s+(?=[A-Za-z_]\w*\s*[,=])",
        text,
        flags=re.IGNORECASE,
    )
    blocks: List[str] = []
    for block in inline_blocks:
        line_parts = re.split(
            r"\n\s*\(?\s*(?:or(?:\s+in\s+python)?|alternatively|another\s+way)\b\s*:?\s*",
            block,
            flags=re.IGNORECASE,
        )
        blocks.extend(part for part in line_parts if part.strip())
    return blocks


def extract_assignment_statements(code_str: str) -> List[str]:
    """
    Pull out only the assignment clauses from an answer.

    Students often describe code in prose, e.g.
    "use a temporary variable: temp = x, then x = y, then y = temp".
    We keep the executable clauses and drop the commentary so the answer can
    be verified by actually running it instead of by keyword guessing.
    """
    text = code_str.replace("\r", "")
    text = _normalize_prose_assignments(text)
    text = _split_run_together_assignments(text)
    statements: List[str] = []

    # Split on explicit statement separators first.
    for part in re.split(r"[;\n]", text):
        part = part.strip()
        if not part:
            continue

        # Only split on commas when several assignments are joined together.
        # A single "x, y = y, x" must stay intact as tuple unpacking.
        clauses = part.split(",") if (part.count("=") > 1 and "," in part) else [part]

        for clause in clauses:
            clause = _clean_clause(clause)
            if not clause or _NEGATED_CLAUSE.match(clause):
                continue

            # Only strip prose connectors when the clause is not already a valid
            # assignment. Otherwise real variables named "first" or "second"
            # would be eaten (first = second would become "= second").
            previous = None
            while clause and previous != clause and not _is_assignment(clause):
                previous = clause
                clause = _LEADING_NOISE.sub("", clause, count=1).strip()

            # "use a temp: temp = x" -> take the part after the colon.
            if ":" in clause:
                after_colon = _clean_clause(clause.split(":")[-1]).strip("()[] ")
                if _is_assignment(after_colon):
                    clause = after_colon

            clause = _clean_clause(clause).strip("()[] ")
            if _is_assignment(clause):
                statements.append(clause)

    return statements


def _is_simple_name(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and not node.id.startswith("__")


def _is_simple_target(node: ast.AST) -> bool:
    if _is_simple_name(node):
        return True
    if isinstance(node, (ast.Tuple, ast.List)):
        return bool(node.elts) and all(_is_simple_target(elt) for elt in node.elts)
    return False


def _is_simple_value(node: ast.AST) -> bool:
    if _is_simple_name(node):
        return True
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List)):
        return all(_is_simple_value(elt) for elt in node.elts)
    return False


def _validate_swap_ast(tree: ast.Module) -> Optional[str]:
    """
    Allow only the safe subset needed for a swap: assignments of names,
    constants, and tuples/lists of those. This is not just a security guard;
    it also gives the student a clear message instead of executing arbitrary
    Python from a learning exercise.
    """
    if not tree.body:
        return "No executable assignment statements were found."
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            return "Only plain assignment statements are supported for this swap."
        if not all(_is_simple_target(target) for target in stmt.targets):
            return "Assignments must target simple variable names."
        if not _is_simple_value(stmt.value):
            return "Assignments must copy simple values or variable names."
    return None


def run_symbolic_code_evaluation(code_str: str, setup_env: Dict[str, Any], goal_check) -> Tuple[bool, str]:
    """
    Executes student code in an isolated dictionary and checks if the state
    transition satisfies the pedagogical goal.

    Returns (success, message). The message "NO_CODE" means the answer was
    prose rather than executable code, so the caller should fall back to
    conceptual grading.
    """
    safe_builtins = {
        "print": print,
        "len": len,
        "range": range,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "abs": abs,
    }

    first_failure = None
    ran_any_code = False

    for block in _split_alternatives(code_str):
        statements = extract_assignment_statements(block)
        if not statements:
            continue
        ran_any_code = True
        code_to_run = "\n".join(statements)

        try:
            tree = ast.parse(code_to_run)
        except SyntaxError as exc:
            if first_failure is None:
                first_failure = f"Syntax error: {exc}. Check that every line is a valid assignment."
            continue

        validation_error = _validate_swap_ast(tree)
        if validation_error:
            if first_failure is None:
                first_failure = validation_error
            continue

        exec_env = {**setup_env}
        try:
            exec(code_to_run, {"__builtins__": safe_builtins}, exec_env)
        except NameError as exc:
            if first_failure is None:
                first_failure = f"NameError: {exc}. You referred to a variable before giving it a value."
            continue
        except Exception as exc:  # noqa: BLE001 - report any runtime mistake to the student
            if first_failure is None:
                first_failure = f"Execution error: {exc}"
            continue

        # Evaluate goal against memory state.
        try:
            success, message = goal_check(setup_env, exec_env)
        except Exception as exc:  # noqa: BLE001
            if first_failure is None:
                first_failure = f"Logic check error: {exc}"
            continue

        if success:
            return True, message
        if first_failure is None:
            first_failure = message

    if not ran_any_code:
        return False, "NO_CODE"
    return False, first_failure or "The code did not achieve the goal."


def check_swap_goal(v1: str, v2: str):
    """Returns a goal checker that verifies if v1 and v2 successfully swapped values without data loss."""
    def _checker(initial_state: Dict[str, Any], final_state: Dict[str, Any]) -> Tuple[bool, str]:
        init_v1 = initial_state[v1]
        init_v2 = initial_state[v2]

        final_v1 = final_state.get(v1)
        final_v2 = final_state.get(v2)

        if final_v1 == init_v2 and final_v2 == init_v1:
            return True, "Logical state verified: Variables swapped values successfully in memory!"
        elif final_v1 == final_v2:
            return False, f"Data lost: Both variables ended up with the same value ({final_v1})!"
        else:
            return False, f"Variables were not swapped. Expected {v1}={init_v2} and {v2}={init_v1}, but got {v1}={final_v1} and {v2}={final_v2}."

    return _checker
