# AI-Powered Adaptive Learning Assistant (Intelligent Tutoring System)

An Intelligent Tutoring System (ITS) implementing personalized student education through:
- **Curriculum Dependency DAG**: Directed Acyclic Graph enforcing strict prerequisite satisfaction.
- **Decoupled Dual Memory**: Complete separation of immutable Subject Knowledge Base (RAG) and private Student Epistemic State.
- **Evidence-Based Knowledge Tracing**: Mathematical mastery updates with statistical confidence calibration and misconception penalties.
- **Targeted Misconception Remediation**: First-class error cataloging with counter-examples and pedagogical routing.

---

## Project Structure

```
mini/
├── app/
│   ├── models/
│   │   ├── concept.py          # Concept, Misconception, KnowledgeChunk
│   │   ├── student.py          # StudentProfile, ConceptMastery, AssessmentLog
│   │   └── curriculum.py       # LearningFrontier, ConceptState, SessionGoal
│   ├── services/
│   │   ├── concept_graph.py    # DAG manager, cycle detector, frontier calculator
│   │   ├── knowledge_base.py   # Ground-truth chunks, citations, retrieval
│   │   ├── student_state.py    # Mathematical knowledge tracing engine
│   │   └── tutor_coordinator.py# Unified pedagogical coordinator
│   └── data/
│       ├── python_concepts.json  # 8-node verified Python curriculum DAG
│       └── python_knowledge.json # Verified textbook & documentation chunks
├── tests/
│   ├── test_concept_graph.py   # DAG validation & cycle detection tests
│   ├── test_mastery_engine.py  # Evidence-based math updates
│   └── test_milestone1_demo.py # End-to-end adaptive frontier progression
└── run_milestone1_demo.py      # Terminal visualization demo
```

---

## Running the Demo

To run the interactive simulation in your terminal:

```powershell
& ".\.venv\Scripts\python.exe" run_milestone1_demo.py
```

## Running the Test Suite

To run the automated test suite with pytest:

```powershell
& ".\.venv\Scripts\python.exe" -m pytest -v
```
