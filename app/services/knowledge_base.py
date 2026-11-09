"""
Knowledge Base Service:
Stores and queries verified, ground-truth educational content chunks.
Ensures factual grounding and produces strict academic/documentation citations.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.models.concept import KnowledgeChunk


class KnowledgeBaseService:
    def __init__(self, knowledge_file: Optional[Path] = None):
        self.chunks: Dict[str, KnowledgeChunk] = {}
        self.concept_to_chunks: Dict[str, List[KnowledgeChunk]] = {}

        if knowledge_file and knowledge_file.exists():
            self.load_from_json(knowledge_file)

    def load_from_json(self, file_path: Path) -> None:
        """Load knowledge chunks from a JSON repository."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Knowledge data must be a JSON list.")

        for item in data:
            chunk = KnowledgeChunk(**item)
            self.add_chunk(chunk)

    def add_chunk(self, chunk: KnowledgeChunk) -> None:
        """Register a knowledge chunk and index it by concept."""
        if chunk.id in self.chunks:
            raise ValueError(f"Duplicate knowledge chunk id: {chunk.id}")
        self.chunks[chunk.id] = chunk
        if chunk.concept_id not in self.concept_to_chunks:
            self.concept_to_chunks[chunk.concept_id] = []
        self.concept_to_chunks[chunk.concept_id].append(chunk)

    def get_chunks_for_concept(self, concept_id: str) -> List[KnowledgeChunk]:
        """Fetch all verified chunks supporting a given concept."""
        return self.concept_to_chunks.get(concept_id, [])

    def validate(self, concept_ids: Optional[Set[str]] = None) -> None:
        """Fail fast when a concept has no cited lesson material."""
        if not self.chunks:
            raise ValueError(
                "No knowledge chunks were loaded. Check app/data/python_knowledge.json."
            )
        if concept_ids is not None:
            missing = sorted(set(concept_ids) - set(self.concept_to_chunks))
            if missing:
                raise ValueError(
                    "Missing knowledge chunks for concept(s): " + ", ".join(missing)
                )
        for chunk in self.chunks.values():
            if not chunk.content.strip():
                raise ValueError(f"Knowledge chunk {chunk.id} has empty content.")
            if not chunk.citations:
                raise ValueError(f"Knowledge chunk {chunk.id} has no citations.")

    def get_chunk(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        """Retrieve a specific chunk by its identifier."""
        return self.chunks.get(chunk_id)

    def search_keyword(self, query: str, top_k: int = 3) -> List[KnowledgeChunk]:
        """
        Lightweight lexical retrieval for Milestone 1 MVP
        (Replaced by pgvector dense retrieval in Milestone 3).
        """
        terms = set(query.lower().split())
        scored: List[tuple[float, KnowledgeChunk]] = []

        for chunk in self.chunks.values():
            content_lower = chunk.content.lower()
            source_lower = chunk.source_title.lower()
            matches = sum(1 for term in terms if term in content_lower or term in source_lower)
            if matches > 0:
                # Weight score by matches and source reliability
                score = (matches / len(terms)) * chunk.reliability_score
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def format_citations(self, chunks: List[KnowledgeChunk]) -> str:
        """Format chunk citations into a standardized bibliography block."""
        lines = []
        for chunk in chunks:
            cites = ", ".join(chunk.citations) if chunk.citations else chunk.source_title
            lines.append(f"- [{chunk.id}] {chunk.source_title} ({chunk.source_author or 'Unknown'}): {cites}")
        return "\n".join(lines)
