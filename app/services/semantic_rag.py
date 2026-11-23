"""
Dense Semantic RAG Service.

Combines:
- High-dimensional dense vector embeddings
- Semantic cosine similarity search
- Provenance and reliability-weighted re-ranking
- Concept-scoped and global knowledge retrieval
- SQLite embedding caching for instant reloads
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from app.models.concept import KnowledgeChunk
from app.models.rag import ScoredChunk, RetrievalQuery, RetrievalResult, IngestionSummary
from app.services.embedding_service import (
    BaseEmbeddingService,
    get_default_embedding_service,
    cosine_similarity,
)
from app.services.student_repository import StudentRepository


class SemanticRAGService:
    """Retrieval-Augmented Generation service powered by dense semantic vectors."""

    def __init__(
        self,
        knowledge_file: Path,
        embedding_service: Optional[BaseEmbeddingService] = None,
        repository: Optional[StudentRepository] = None,
    ):
        self.knowledge_file = Path(knowledge_file)
        self.embedding_service = embedding_service or get_default_embedding_service()
        self.repository = repository

        self.chunks_by_id: Dict[str, KnowledgeChunk] = {}
        self.chunks_by_concept: Dict[str, List[KnowledgeChunk]] = {}
        self.chunk_vectors: Dict[str, List[float]] = {}

        self.load_and_index()

    def _hash_content(self, chunk: KnowledgeChunk) -> str:
        raw = f"{chunk.id}|{chunk.concept_id}|{chunk.content}|{chunk.source_title}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def load_and_index(self) -> None:
        """Load knowledge chunks and compute/load dense embeddings."""
        if not self.knowledge_file.exists():
            raise FileNotFoundError(f"Knowledge file not found: {self.knowledge_file}")

        with open(self.knowledge_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.chunks_by_id.clear()
        self.chunks_by_concept.clear()

        # Group and index chunks
        for entry in raw_data:
            chunk = KnowledgeChunk(**entry)
            self.chunks_by_id[chunk.id] = chunk
            self.chunks_by_concept.setdefault(chunk.concept_id, []).append(chunk)

        # Check cached embeddings from SQLite
        cached_embeddings: Dict[str, Dict] = {}
        if self.repository is not None:
            cached_embeddings = self.repository.load_chunk_embeddings(
                provider_name=self.embedding_service.provider_name
            )

        # Compute embeddings for any missing or changed chunks
        for chunk in self.chunks_by_id.values():
            c_hash = self._hash_content(chunk)
            cached = cached_embeddings.get(chunk.id)

            if cached and cached.get("content_hash") == c_hash:
                self.chunk_vectors[chunk.id] = cached["embedding"]
            else:
                # Text for embedding includes concept, title, and verified content
                embed_input = f"{chunk.concept_id}: {chunk.source_title}\n{chunk.content}"
                vector = self.embedding_service.embed_text(embed_input)
                self.chunk_vectors[chunk.id] = vector

                if self.repository is not None:
                    self.repository.save_chunk_embedding(
                        chunk_id=chunk.id,
                        concept_id=chunk.concept_id,
                        provider_name=self.embedding_service.provider_name,
                        dimension=self.embedding_service.dimension,
                        embedding=vector,
                        content_hash=c_hash,
                    )

    def retrieve(
        self,
        query: str,
        concept_id: Optional[str] = None,
        top_k: int = 3,
        min_similarity: float = 0.0,
    ) -> RetrievalResult:
        """Perform dense semantic vector retrieval over knowledge chunks."""
        start_time = time.perf_counter()

        if not query or not query.strip():
            # If query is empty, return concept-scoped chunks directly if available
            fallback_chunks = self.get_concept_ground_truth(concept_id) if concept_id else []
            matches = [
                ScoredChunk(
                    chunk=c,
                    similarity_score=1.0,
                    reliability_weighted_score=c.reliability_score,
                    retrieval_method="lexical",
                )
                for c in fallback_chunks[:top_k]
            ]
            return RetrievalResult(
                query=query,
                concept_filter=concept_id,
                matches=matches,
                retrieval_time_ms=(time.perf_counter() - start_time) * 1000,
                embedding_dimension=self.embedding_service.dimension,
            )

        query_vec = self.embedding_service.embed_text(query)

        # Determine candidate chunk pool
        if concept_id and concept_id in self.chunks_by_concept:
            candidates = self.chunks_by_concept[concept_id]
        else:
            candidates = list(self.chunks_by_id.values())

        scored_candidates: List[ScoredChunk] = []
        for chunk in candidates:
            chunk_vec = self.chunk_vectors.get(chunk.id)
            if not chunk_vec:
                continue

            raw_sim = cosine_similarity(query_vec, chunk_vec)
            # Rescale negative cosine similarities to 0 for pedagogical ranking
            sim = max(0.0, raw_sim)

            if sim >= min_similarity:
                weighted_score = sim * chunk.reliability_score
                scored_candidates.append(
                    ScoredChunk(
                        chunk=chunk,
                        similarity_score=sim,
                        reliability_weighted_score=weighted_score,
                        retrieval_method="dense_vector",
                    )
                )

        # Sort primarily by reliability-weighted score, then by raw similarity
        scored_candidates.sort(
            key=lambda x: (x.reliability_weighted_score, x.similarity_score),
            reverse=True,
        )

        top_matches = scored_candidates[:top_k]
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return RetrievalResult(
            query=query,
            concept_filter=concept_id,
            matches=top_matches,
            retrieval_time_ms=elapsed_ms,
            embedding_dimension=self.embedding_service.dimension,
        )

    def get_concept_ground_truth(self, concept_id: str) -> List[KnowledgeChunk]:
        """Return all authoritative chunks directly tied to a concept."""
        return self.chunks_by_concept.get(concept_id, [])

    def format_context_for_prompt(self, chunks: List[ScoredChunk]) -> str:
        """Format retrieved chunks into clean markdown for Socratic LLM grounding."""
        if not chunks:
            return "No specific reference chunks retrieved."

        lines = ["### Verified Subject Ground Truth (Authoritative References):"]
        for idx, item in enumerate(chunks, 1):
            c = item.chunk
            lines.append(f"\n[Reference {idx}: {c.source_title}]")
            lines.append(f"- Reliability Score: {c.reliability_score:.2f} | Semantic Match: {item.similarity_score:.2f}")
            if c.citations:
                lines.append(f"- Citations: {'; '.join(c.citations)}")
            lines.append(f"- Factual Content: {c.content}")

        return "\n".join(lines)

    def ingest_document(
        self,
        file_path: Union[str, Path],
        linker: Optional[Any] = None,
        default_concept_id: str = "py.variables",
    ) -> IngestionSummary:
        """Dynamically ingest a Markdown or PDF document, auto-link to DAG concepts, and index."""
        from app.services.document_ingestion import DocumentIngestionService

        ingestion_service = DocumentIngestionService()
        chunks, summary = ingestion_service.ingest_file(file_path)

        if linker is not None:
            linker.link_batch(chunks)

        # Convert to KnowledgeChunks
        knowledge_chunks = [c.to_knowledge_chunk(fallback_concept_id=default_concept_id) for c in chunks]

        # Compute embeddings
        contents = [kc.content for kc in knowledge_chunks]
        embeddings = self.embedding_service.embed_batch(contents)

        for kc, emb in zip(knowledge_chunks, embeddings):
            self.chunks_by_id[kc.id] = kc
            if kc.concept_id not in self.chunks_by_concept:
                self.chunks_by_concept[kc.concept_id] = []
            self.chunks_by_concept[kc.concept_id].append(kc)
            self.chunk_vectors[kc.id] = emb

            if self.repository is not None:
                h = self._hash_content(kc)
                self.repository.save_chunk_embedding(
                    chunk_id=kc.id,
                    concept_id=kc.concept_id,
                    provider_name=self.embedding_service.provider_name,
                    dimension=self.embedding_service.dimension,
                    embedding=emb,
                    content_hash=h,
                )

        summary.linked_chunks = sum(1 for c in chunks if c.concept_id)
        summary.unlinked_chunks = sum(1 for c in chunks if not c.concept_id)
        return summary

