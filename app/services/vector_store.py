"""
Vector Store Service:
Provides unified dense vector embedding storage and cosine similarity retrieval
supporting both PostgreSQL with the pgvector extension and local SQLite storage.
"""
from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
import sqlite3
import struct
from typing import List, Dict, Tuple, Optional, Any, Union

from app.models.concept import KnowledgeChunk
from app.services.embedding_service import cosine_similarity, normalize_vector

try:
    import pgvector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class BaseVectorStore(ABC):
    """Abstract interface for dense vector embedding stores."""

    @abstractmethod
    def add_chunks(
        self,
        chunks: List[KnowledgeChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Store chunks and their vector embeddings."""
        pass

    @abstractmethod
    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        concept_id: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """Return the top_k most similar chunks with their cosine similarity scores."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of indexed vectors."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Delete all vectors and chunks."""
        pass


class SQLiteVectorStore(BaseVectorStore):
    """Local, zero-dependency SQLite-backed vector store with BLOB-encoded vectors."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = str(db_path or ":memory:")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunk_vectors (
                    id TEXT PRIMARY KEY,
                    concept_id TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    reliability_score REAL NOT NULL,
                    content TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    embedding_blob BLOB NOT NULL,
                    dimension INTEGER NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_concept ON chunk_vectors(concept_id);")
            conn.commit()

    @staticmethod
    def _pack_vector(vector: List[float]) -> bytes:
        return struct.pack(f"{len(vector)}f", *vector)

    @staticmethod
    def _unpack_vector(blob: bytes, dimension: int) -> List[float]:
        return list(struct.unpack(f"{dimension}f", blob))

    def add_chunks(
        self,
        chunks: List[KnowledgeChunk],
        embeddings: List[List[float]],
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings lists must be equal in length.")

        inserted = 0
        with self._get_connection() as conn:
            for chunk, emb in zip(chunks, embeddings):
                norm_emb = normalize_vector(emb)
                blob = self._pack_vector(norm_emb)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunk_vectors (
                        id, concept_id, source_title, source_type,
                        reliability_score, content, citations_json, embedding_blob, dimension
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk.id,
                        chunk.concept_id,
                        chunk.source_title,
                        chunk.source_type,
                        chunk.reliability_score,
                        chunk.content,
                        json.dumps(chunk.citations),
                        blob,
                        len(norm_emb),
                    ),
                )
                inserted += 1
            conn.commit()
        return inserted

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        concept_id: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        norm_query = normalize_vector(query_vector)
        candidates = []

        query_sql = "SELECT * FROM chunk_vectors"
        params: List[Any] = []
        if concept_id:
            query_sql += " WHERE concept_id = ?"
            params.append(concept_id)

        with self._get_connection() as conn:
            rows = conn.execute(query_sql, params).fetchall()
            for row in rows:
                dim = row["dimension"]
                emb = self._unpack_vector(row["embedding_blob"], dim)
                sim = cosine_similarity(norm_query, emb)
                if sim >= min_similarity:
                    chunk = KnowledgeChunk(
                        id=row["id"],
                        concept_id=row["concept_id"],
                        source_title=row["source_title"],
                        source_type=row["source_type"],
                        reliability_score=row["reliability_score"],
                        content=row["content"],
                        citations=json.loads(row["citations_json"]),
                    )
                    candidates.append((chunk, sim))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def count(self) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM chunk_vectors;").fetchone()
            return row["cnt"] if row else 0

    def clear(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunk_vectors;")
            conn.commit()


class PGVectorStore(BaseVectorStore):
    """
    PostgreSQL Vector Store powered by the pgvector extension.
    Executes native HNSW/IVFFlat cosine similarity searches.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        dimension: int = 128,
        table_name: str = "knowledge_chunks",
    ):
        self.conn_str = connection_string or os.environ.get("DATABASE_URL") or os.environ.get("PG_CONNECTION_STRING", "")
        self.dimension = dimension
        self.table_name = table_name

    @classmethod
    def get_schema_ddl(cls, dimension: int = 128, table_name: str = "knowledge_chunks") -> str:
        """Return the PostgreSQL DDL commands for setting up pgvector and tables."""
        return f"""
-- 1. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the knowledge chunk embeddings table
CREATE TABLE IF NOT EXISTS {table_name} (
    id VARCHAR(128) PRIMARY KEY,
    concept_id VARCHAR(64) NOT NULL,
    source_title TEXT NOT NULL,
    source_type VARCHAR(32) NOT NULL DEFAULT 'textbook',
    reliability_score FLOAT NOT NULL DEFAULT 1.0,
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    embedding vector({dimension})
);

-- 3. Create HNSW cosine similarity index for sub-millisecond retrieval
CREATE INDEX IF NOT EXISTS idx_{table_name}_vector_hnsw 
ON {table_name} USING hnsw (embedding vector_cosine_ops);

-- 4. Create B-Tree index for concept scoping
CREATE INDEX IF NOT EXISTS idx_{table_name}_concept 
ON {table_name} (concept_id);
"""

    def add_chunks(
        self,
        chunks: List[KnowledgeChunk],
        embeddings: List[List[float]],
    ) -> int:
        if not self.conn_str:
            raise ConnectionError("PostgreSQL connection string is not configured.")

        try:
            import psycopg
        except ImportError:
            try:
                import psycopg2 as psycopg
            except ImportError:
                raise ImportError("psycopg or psycopg2 is required to connect to pgvector.")

        inserted = 0
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(self.get_schema_ddl(self.dimension, self.table_name))
                for chunk, emb in zip(chunks, embeddings):
                    norm_emb = normalize_vector(emb)
                    cur.execute(
                        f"""
                        INSERT INTO {self.table_name} (
                            id, concept_id, source_title, source_type,
                            reliability_score, content, citations, embedding
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding;
                        """,
                        (
                            chunk.id,
                            chunk.concept_id,
                            chunk.source_title,
                            chunk.source_type,
                            chunk.reliability_score,
                            chunk.content,
                            json.dumps(chunk.citations),
                            norm_emb,
                        ),
                    )
                    inserted += 1
                conn.commit()
        return inserted

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        concept_id: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        if not self.conn_str:
            raise ConnectionError("PostgreSQL connection string is not configured.")

        try:
            import psycopg
        except ImportError:
            import psycopg2 as psycopg

        norm_query = normalize_vector(query_vector)
        results = []

        where_clause = ""
        params: List[Any] = [norm_query]
        if concept_id:
            where_clause = "WHERE concept_id = %s"
            params.append(concept_id)

        sql = f"""
        SELECT id, concept_id, source_title, source_type, reliability_score, content, citations,
               1 - (embedding <=> %s::vector) AS similarity
        FROM {self.table_name}
        {where_clause}
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """
        params.extend([norm_query, top_k])

        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                for row in cur.fetchall():
                    sim = float(row[7])
                    if sim >= min_similarity:
                        chunk = KnowledgeChunk(
                            id=row[0],
                            concept_id=row[1],
                            source_title=row[2],
                            source_type=row[3],
                            reliability_score=float(row[4]),
                            content=row[5],
                            citations=json.loads(row[6]) if isinstance(row[6], str) else row[6],
                        )
                        results.append((chunk, sim))
        return results

    def count(self) -> int:
        if not self.conn_str:
            return 0
        try:
            import psycopg
        except ImportError:
            import psycopg2 as psycopg
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {self.table_name};")
                row = cur.fetchone()
                return int(row[0]) if row else 0

    def clear(self) -> None:
        if not self.conn_str:
            return
        try:
            import psycopg
        except ImportError:
            import psycopg2 as psycopg
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {self.table_name};")
                conn.commit()


def create_vector_store(
    backend: str = "auto",
    db_path: Optional[Union[str, Path]] = None,
    pg_connection_string: Optional[str] = None,
    dimension: int = 128,
) -> BaseVectorStore:
    """Factory creating vector store with pgvector when available or resilient SQLite."""
    pg_url = pg_connection_string or os.environ.get("DATABASE_URL") or os.environ.get("PG_CONNECTION_STRING")
    if (backend == "pgvector" or (backend == "auto" and pg_url)) and HAS_PGVECTOR and pg_url:
        try:
            pg_store = PGVectorStore(connection_string=pg_url, dimension=dimension)
            return pg_store
        except Exception:
            # Fall back to SQLite if Postgres connection fails
            pass

    return SQLiteVectorStore(db_path=db_path)
