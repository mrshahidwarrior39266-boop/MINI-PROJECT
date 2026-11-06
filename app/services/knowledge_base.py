"""
Knowledge Base Service:
Stores and queries verified, ground-truth educational content chunks.
Ensures factual grounding and produces strict academic/documentation citations.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

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

        for item in data:
            chunk = KnowledgeChunk(**item)
            self.add_chunk(chunk)

    def add_chunk(self, chunk: KnowledgeChunk) -> None:
        """Register a knowledge chunk and index it by concept."""
        self.chunks[chunk.id] = chunk
        if chunk.concept_id not in self.concept_to_chunks:
            self.concept_to_chunks[chunk.concept_id] = []
        self.concept_to_chunks[chunk.concept_id].append(chunk)

    def get_chunks_for_concept(self, concept_id: str) -> List[KnowledgeChunk]:
        """Fetch all verified chunks supporting a given concept."""
        return self.concept_to_chunks.get(concept_id, [])

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
