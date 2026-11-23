"""
Concept Linker Service:
Runs an LLM extraction pass on unlinked document chunks to map them
into the curriculum DAG concepts with structured confidence, rationale, and takeaways.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from app.models.concept import Concept
from app.models.rag import DocumentChunk, ConceptLinkageResult
from app.services.llm_client import BaseLLMClient, get_default_llm_client, MockLLMClient


class ConceptLinkerService:
    """Classifies and links document chunks to curriculum concepts using LLM extraction."""

    def __init__(
        self,
        concepts_catalog: Dict[str, Concept],
        llm_client: Optional[BaseLLMClient] = None,
    ):
        self.concepts = concepts_catalog
        self.llm_client = llm_client or get_default_llm_client()

    @classmethod
    def from_concepts_file(
        cls,
        concepts_file: Path,
        llm_client: Optional[BaseLLMClient] = None,
    ) -> "ConceptLinkerService":
        """Factory initializing catalog from a python_concepts.json file."""
        with open(concepts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        catalog = {item["id"]: Concept(**item) for item in data}
        return cls(concepts_catalog=catalog, llm_client=llm_client)

    def link_chunk(self, chunk: DocumentChunk) -> ConceptLinkageResult:
        """Run an LLM extraction pass to classify and link a chunk to the curriculum graph."""
        prompt = self._build_extraction_prompt(chunk)

        # Attempt structured output via LLM client
        if self.llm_client:
            try:
                result: ConceptLinkageResult = self.llm_client.generate_structured(
                    prompt=prompt,
                    response_model=ConceptLinkageResult,
                    system_prompt=(
                        "You are an expert curriculum architect. Your role is to analyze pedagogical "
                        "textbook chunks and link them to the authoritative concept nodes in the curriculum DAG."
                    ),
                    temperature=0.0,
                )
                # Verify that returned primary_concept_id exists in graph
                if result.primary_concept_id and result.primary_concept_id in self.concepts:
                    chunk.concept_id = result.primary_concept_id
                    chunk.metadata["linkage_confidence"] = result.confidence
                    chunk.metadata["secondary_concepts"] = result.secondary_concept_ids
                    return result
            except Exception:
                # LLM extraction failed; fall back to deterministic semantic rule mapping
                pass

        # Deterministic offline rule fallback
        fallback = self._deterministic_link_chunk(chunk)
        chunk.concept_id = fallback.primary_concept_id
        chunk.metadata["linkage_confidence"] = fallback.confidence
        chunk.metadata["secondary_concepts"] = fallback.secondary_concept_ids
        return fallback

    def link_batch(self, chunks: List[DocumentChunk]) -> List[ConceptLinkageResult]:
        """Classify and link a batch of chunks."""
        return [self.link_chunk(c) for c in chunks]

    def _build_extraction_prompt(self, chunk: DocumentChunk) -> str:
        """Construct the prompt containing curriculum catalog and chunk text."""
        catalog_lines = []
        for cid, concept in self.concepts.items():
            objs = ", ".join(concept.learning_objectives[:3])
            catalog_lines.append(f"  - Concept ID: '{cid}' | Title: '{concept.title}' | Objectives: {objs}")

        heading_info = " > ".join(chunk.heading_path) if chunk.heading_path else "Top-level Section"

        return f"""
You are given a document excerpt from '{chunk.source}' under section '{heading_info}'.

AVAILABLE CURRICULUM CONCEPTS IN THE GRAPH:
{chr(10).join(catalog_lines)}

DOCUMENT EXCERPT:
\"\"\"
{chunk.content}
\"\"\"

TASK:
1. Identify the single best PRIMARY concept ID from the list above that this excerpt teaches.
2. If this text introduces secondary concepts as prerequisites or applications, list them.
3. Assign a confidence score from 0.0 to 1.0.
4. Extract 1-3 core pedagogical takeaways.
5. Identify if any common student misconceptions are described.
6. Provide brief rationale.
"""

    def _deterministic_link_chunk(self, chunk: DocumentChunk) -> ConceptLinkageResult:
        """Deterministic heuristic mapper for offline / mock resilience."""
        text = (
            " ".join(chunk.heading_path) + " " + chunk.content + " " + chunk.source
        ).lower()

        scores: Dict[str, float] = {}

        keyword_map = {
            "py.variables": [
                "variable", "assign", "assignment", "name binding", "memory box",
                "rebind", "swap", "identifier", "value", "=",
            ],
            "py.data_types": [
                "data type", "integer", "float", "string", "boolean", "type",
                "str", "int", "float", "bool", "type conversion",
            ],
            "py.operators": [
                "operator", "arithmetic", "modulo", "floor division", "//", "%",
                "precedence", "comparison", "equality", "==", "!=",
            ],
            "py.conditionals": [
                "conditional", "if", "elif", "else", "branching", "boolean expression",
                "truth value", "indentation",
            ],
            "py.while_loops": [
                "while", "infinite loop", "termination", "condition", "break",
                "sentinel", "loop body",
            ],
            "py.for_loops": [
                "for loop", "iterate", "iteration", "range", "sequence", "traversal",
                "counter", "in range",
            ],
            "py.lists_sequences": [
                "list", "indexing", "slice", "element", "append", "zero-indexed",
                "square brackets", "mutable", "sequence",
            ],
            "py.functions": [
                "def ", "function", "parameter", "argument", "return", "scope",
                "call stack", "modular",
            ],
        }

        for cid, keywords in keyword_map.items():
            if cid not in self.concepts:
                continue
            matched = sum(1 for kw in keywords if kw in text)
            # Give extra weight to keywords appearing in headings
            h_text = " ".join(chunk.heading_path).lower()
            h_matched = sum(2 for kw in keywords if kw in h_text)
            scores[cid] = (matched + h_matched) / (len(keywords) + 2)

        best_cid = max(scores, key=scores.get) if scores else "py.variables"
        best_score = scores.get(best_cid, 0.0)
        confidence = min(1.0, max(0.5, best_score * 2.5))

        # Secondary concepts
        secondaries = [
            cid for cid, s in scores.items() if cid != best_cid and s >= 0.2
        ][:2]

        return ConceptLinkageResult(
            chunk_id=chunk.id,
            primary_concept_id=best_cid,
            secondary_concept_ids=secondaries,
            confidence=round(confidence, 2),
            reasoning=f"Matched concept '{self.concepts[best_cid].title}' based on technical keyword density.",
            key_takeaways=[
                f"Core mechanism explained in section {' > '.join(chunk.heading_path)}.",
                f"Mapped directly to curriculum node: {best_cid}.",
            ],
            detected_misconceptions=[],
        )
