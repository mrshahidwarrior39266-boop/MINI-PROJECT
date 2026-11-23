

# AI-Powered Adaptive Learning Assistant (Intelligent Tutoring System)

An Intelligent Tutoring System (ITS) implementing personalized student education through:
- **Curriculum Dependency DAG**: Directed Acyclic Graph enforcing strict prerequisite satisfaction.
- **Decoupled Dual Memory**: Complete separation of immutable Subject Knowledge Base (RAG) and private Student Epistemic State.
- **Evidence-Based Knowledge Tracing**: Mathematical mastery updates with statistical confidence calibration and misconception penalties.
- **Targeted Misconception Remediation**: First-class error cataloging with counter-examples and pedagogical routing.
- **Never-Stuck Tutoring**: A missed question leads to a transfer follow-up; a second miss leads to guided micro-steps with immediate hints.

> **Status:** Milestone 1 (Concept DAG & Adaptive Mastery) and Milestone 2 (Dense Semantic RAG, Socratic LLM Evaluator, Zero-Knowledge Beginner Pedagogy, Memory Visualizer & Verifiable Transcripts) are 100% complete and fully verified across all 8 lessons with 320 unit/integration tests.

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

## Demos

### Milestone 1: Adaptive Learning Frontier & Remediation
```powershell
& ".\.venv\Scripts\python.exe" run_milestone1_demo.py
```

### Milestone 2: Dense Semantic RAG & Socratic LLM Evaluator
```powershell
& ".\.venv\Scripts\python.exe" run_milestone2_demo.py
```

### Milestone 3: Dynamic Knowledge Ingestion & pgvector RAG
```powershell
& ".\.venv\Scripts\python.exe" run_milestone3_demo.py
```

## Running the Test Suite

```powershell
& ".\.venv\Scripts\python.exe" -m pytest -v
```

---

## How Milestone 2 Operates (Dense Semantic RAG & Socratic LLM)

- **Dense Semantic Vector RAG**: Precomputes high-dimensional dense embeddings for authoritative curriculum textbook chunks with subword n-grams and programming operator awareness. Performs cosine similarity retrieval with provenance and source reliability re-ranking.
- **SQLite Vector Caching**: Chunks are cached in `chunk_embeddings` table to ensure instantaneous sub-millisecond retrieval on repeat runs.
- **Socratic LLM Evaluator**: When configured with `GEMINI_API_KEY` or `OPENAI_API_KEY`, evaluations are performed using structured Pydantic schemas (`LLMEvaluationResponse`), grounding explanations in retrieved textbook excerpts and categorizing mistakes into formal cataloged misconceptions.
- **Logic Invariant Guarantee**: The AST Logic Verifier checks computational state transitions in memory. A student who writes `t=x,x=y,y=t` is guaranteed 100% credit regardless of variable names, preventing LLM optimism or formatting bias.
- **Fault-Tolerant Fallback**: If network is unavailable or no API keys are present, the system seamlessly routes to the deterministic rule and AST verifier with zero crashes.

---

## How Milestone 3 Operates (Dynamic Ingestion & pgvector RAG)

- **Semantic Heading-Based Chunking**: The `DocumentIngestionService` parses Markdown (`#`, `##`, `###`) and PDF section structures, splitting texts into meaningful pedagogical units while preserving code blocks and breadcrumb heading hierarchies rather than slicing across arbitrary character boundaries.
- **LLM Concept Auto-Linker**: The `ConceptLinkerService` executes an extraction pass over unlinked document chunks, using LLM structured extraction to map each section to the correct curriculum DAG node with pedagogical rationale and confidence scoring.
- **pgvector Vector Store**: Implements the `PGVectorStore` backend with native PostgreSQL `vector(128)` and HNSW cosine similarity indexing (`vector_cosine_ops`), accompanied by `SQLiteVectorStore` for zero-dependency local execution.
- **Enforced Source Citations**: The Socratic `LLMEvaluator` enforces that evaluations must cite specific `chunk_id` foreign keys from the ingested knowledge base, ensuring evidence grounding and verifiable provenance.

---

## Project Structure

```
mini/
├── app/
│   ├── models/
│   │   ├── concept.py            # Concept, Misconception, KnowledgeChunk
│   │   ├── student.py            # StudentProfile, ConceptMastery, AssessmentLog
│   │   ├── curriculum.py         # LearningFrontier, ConceptState, SessionGoal
│   │   ├── question.py           # Questions, rubrics, follow-ups, scaffold steps
│   │   ├── rag.py                # ScoredChunk, RetrievalQuery, RetrievalResult
│   │   └── evaluator.py          # LLMEvaluationRequest, LLMEvaluationResponse
│   ├── services/
│   │   ├── concept_graph.py      # DAG manager, cycle detector, frontier calculator
│   │   ├── knowledge_base.py     # Ground-truth chunks, citations, retrieval
│   │   ├── student_state.py      # Mathematical knowledge tracing engine
│   │   ├── student_repository.py # SQLite ACID persistence for student profiles & cursors
│   │   ├── tutor_coordinator.py  # Unified pedagogical coordinator
│   │   ├── question_service.py   # Boundary-aware rubric grading
│   │   ├── logic_verifier.py     # Executes and verifies student swap code
│   │   ├── embedding_service.py  # Dense vector embeddings (Gemini, OpenAI, Deterministic)
│   │   ├── semantic_rag.py       # Dense RAG vector search & prompt context builder
│   │   ├── llm_client.py         # Gemini, OpenAI, and Mock LLM client backends
│   │   ├── llm_evaluator.py      # Socratic evaluator with RAG grounding & fallback
│   │   ├── beginner_pedagogy.py  # Zero-knowledge physical models & 3-second mental movies
│   │   ├── memory_visualizer.py  # ASCII RAM box diagrams and memory state transitions
│   │   └── mastery_reporter.py   # Verifiable student transcripts with SHA-256 audit seal
│   └── data/
│       ├── python_concepts.json      # 8-concept verified Python curriculum DAG
│       ├── python_knowledge.json     # Verified textbook & documentation chunks
│       ├── curriculum_questions.json # Questions, follow-ups, scaffolding steps
│       └── beginner_analogies.json   # Real-world physical analogies for all 8 concepts
├── tests/
│   ├── test_all_lessons_milestone2.py# Milestone 2 verification across all 8 curriculum lessons
│   ├── test_beginner_pedagogy.py     # Physical analogies & mental movie tests
│   ├── test_concept_graph.py
│   ├── test_curriculum_integrity.py
│   ├── test_dense_rag.py             # Vector math, cosine ranking, SQLite embedding cache
│   ├── test_interactive_tutor.py     # End-to-end CLI behavior, persistence, and resume
│   ├── test_llm_evaluator.py         # Socratic structured evaluation, RAG grounding, fallbacks
│   ├── test_logic_verifier.py        # Isolated AST state evaluation
│   ├── test_mastery_engine.py        # Mathematical knowledge tracing
│   ├── test_mastery_reporter.py      # Verifiable transcript & SHA-256 fingerprint tests
│   ├── test_memory_visualizer.py     # RAM box diagrams & swap movie tests
│   ├── test_milestone1_demo.py       # Milestone 1 adaptive progression
│   ├── test_milestone2_demo.py       # Milestone 2 RAG & Socratic demo
│   ├── test_persistence.py           # SQLite persistence CRUD and reloads
│   ├── test_response_quality.py      # Beginner phrasings and grading regressions
│   └── test_swap_formats.py          # Multi-syntax swap validation
├── interactive_tutor.py
├── run_milestone1_demo.py
├── run_milestone2_demo.py
└── requirements.txt
```
