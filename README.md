# AI-Powered Adaptive Learning Assistant (Intelligent Tutoring System)

An Intelligent Tutoring System (ITS) implementing personalized student education through:
- **Curriculum Dependency DAG**: Directed Acyclic Graph enforcing strict prerequisite satisfaction.
- **Decoupled Dual Memory**: Complete separation of immutable Subject Knowledge Base (RAG) and private Student Epistemic State.
- **Evidence-Based Knowledge Tracing**: Mathematical mastery updates with statistical confidence calibration and misconception penalties.
- **Targeted Misconception Remediation**: First-class error cataloging with counter-examples and pedagogical routing.
- **Never-Stuck Tutoring**: A missed question leads to a transfer follow-up; a second miss leads to guided micro-steps with immediate hints.

> Milestone 1 keeps the learner state in memory for the current session. Progress is intentionally not persisted between runs yet.

---

## Quick Start

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

## Interactive Tutor (the main student experience)

```powershell
& ".\.venv\Scripts\python.exe" interactive_tutor.py
```

- 8-concept Python curriculum with lesson bites, cited sources, and a progress dashboard.
- Each concept needs 70% mastery. Mastery grows with evidence, so a concept with one question asks you to practise it again (the tutor labels this as a review round).
- Wrong answer? You get the reference answer, a step-by-step explanation, a transfer challenge, and targeted misconception feedback.
- Wrong twice? Guided scaffolding walks you through atomic micro-steps until the walkthrough is complete. This is guided practice, not an automatic mastery award: the 70% threshold still requires evidence.
- Every concept has a cited lesson bite, and curriculum data is validated at startup (no missing questions, chunks, or misconception IDs).
- `quit` / `exit` ends the session. A blank answer re-prompts instead of quitting. `restart` / `reset` starts over.

## Demo

```powershell
& ".\.venv\Scripts\python.exe" run_milestone1_demo.py
```

## Running the Test Suite

```powershell
& ".\.venv\Scripts\python.exe" -m pytest -v
```

---

## How Grading Works

- Rubric keywords use word and number boundaries, so `4` does not match `4.5`, `b` does not match `because`, and `10` does not match `100`.
- Negated phrases are respected: "it is **not** 10, it is 55 because strings are glued" is correctly treated as a correct answer.
- Comparison questions require both sides of the comparison (for example, `/` gives 3.5 **and** `//` gives 3). One-sided answers earn half credit and a request to complete the explanation.
- Code answers are executed in a separate namespace restricted to plain assignments and checked by state. This is a teaching sandbox, not a general-purpose Python runtime. `temp = x; x = y; y = temp`, `x, y = y, x`, and prose like "save x in temp, copy y into x, then put temp into y" are all accepted.
- Bare keyword stuffing is rejected; substantive reasoning is required. Follow-up answers must also be complete: the swap transfer challenge requires all three steps, not a single keyword.
- Known mistakes map to real misconception IDs in each concept's catalog. Startup validation rejects dangling IDs, and the remediation briefing resolves the specific name, description, and hint.
- The current evaluator is deterministic and local. It does not call an external LLM or require an API key.

---

## Project Structure

```
mini/
├── app/
│   ├── models/
│   │   ├── concept.py            # Concept, Misconception, KnowledgeChunk
│   │   ├── student.py            # StudentProfile, ConceptMastery, AssessmentLog
│   │   ├── curriculum.py         # LearningFrontier, ConceptState, SessionGoal
│   │   └── question.py           # Questions, rubrics, follow-ups, scaffold steps
│   ├── services/
│   │   ├── concept_graph.py      # DAG manager, cycle detector, frontier calculator
│   │   ├── knowledge_base.py     # Ground-truth chunks, citations, retrieval
│   │   ├── student_state.py      # Mathematical knowledge tracing engine
│   │   ├── tutor_coordinator.py  # Unified pedagogical coordinator
│   │   ├── question_service.py   # Boundary-aware rubric grading
│   │   └── logic_verifier.py     # Executes and verifies student swap code
│   └── data/
│       ├── python_concepts.json      # 8-concept verified Python curriculum DAG
│       ├── python_knowledge.json     # Verified textbook & documentation chunks
│       └── curriculum_questions.json # Questions, follow-ups, scaffolding steps
├── tests/
│   ├── test_concept_graph.py
│   ├── test_mastery_engine.py
│   ├── test_milestone1_demo.py
│   ├── test_logic_verifier.py
│   ├── test_swap_formats.py          # Format matrix for the swap parser
│   ├── test_response_quality.py      # Beginner phrasings and grading regressions
│   ├── test_interactive_tutor.py     # End-to-end CLI behavior
│   ├── test_curriculum_integrity.py  # Data invariants before startup
│   └── data/full_playthrough_input.txt
├── interactive_tutor.py
├── run_milestone1_demo.py
└── requirements.txt
```
