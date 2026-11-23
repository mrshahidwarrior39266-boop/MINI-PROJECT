"""
Dense Semantic Embedding Services.

Provides:
- BaseEmbeddingService: Abstract protocol for text embedding
- DeterministicSemanticEmbedding: Zero-dependency, offline, subword & semantic hashing vector engine
- GeminiEmbeddingService: Google Gemini embedding provider (text-embedding-004)
- OpenAIEmbeddingService: OpenAI embedding provider (text-embedding-3-small)
- Math utilities: cosine_similarity, normalize_vector
"""
from abc import ABC, abstractmethod
import hashlib
import json
import math
import os
import re
from typing import List, Optional
import urllib.request
import urllib.error


def normalize_vector(v: List[float]) -> List[float]:
    """Normalize a vector to unit length (L2 norm = 1.0)."""
    norm = math.sqrt(sum(x * x for x in v))
    if norm < 1e-12:
        return [0.0] * len(v)
    return [x / norm for x in v]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors. Returns float in [-1.0, 1.0]."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    denom = norm_a * norm_b
    if denom < 1e-12:
        return 0.0
    val = dot / denom
    return max(-1.0, min(1.0, val))


class BaseEmbeddingService(ABC):
    """Abstract interface for dense embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimensionality."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string into a normalized dense vector."""
        pass

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        return [self.embed_text(t) for t in texts]


class DeterministicSemanticEmbedding(BaseEmbeddingService):
    """
    High-dimensional deterministic semantic feature-hashing embedding engine.
    
    Guarantees:
    - 100% offline, zero-dependency, platform-independent.
    - Captures morphological subword n-grams and programming domain semantics.
    - Consistently assigns high similarity to conceptually aligned educational queries.
    """

    STOPWORDS = {
        "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
        "and", "or", "is", "are", "was", "were", "it", "its", "this", "that",
        "do", "does", "did", "can", "could", "would", "should", "will", "what"
    }

    # Semantic anchor keywords mapped to high-weight domain prototypes
    SEMANTIC_ANCHORS = {
        "variable": [
            "variable", "variables", "assign", "assignment", "assignments", "name",
            "value", "values", "bind", "binding", "store", "storing", "memory", "box",
            "reference", "references", "op_assign"
        ],
        "assign": [
            "equal", "equals", "assignment", "assignments", "statement", "statements",
            "copy", "overwrite", "bind", "swap", "swapping", "temp", "op_assign"
        ],
        "type": [
            "integer", "integers", "float", "floats", "string", "strings", "boolean",
            "booleans", "str", "int", "bool", "cast", "type", "types", "conversion"
        ],
        "operator": [
            "add", "subtract", "multiply", "divide", "floor", "modulo", "precedence",
            "eval", "op_add", "op_sub", "op_mul", "op_div", "op_floordiv", "op_mod"
        ],
        "condition": [
            "if", "elif", "else", "branch", "branching", "comparison", "boolean",
            "true", "false", "op_equals", "op_notequals"
        ],
        "loop": [
            "for", "while", "iterate", "iteration", "iterations", "loop", "loops",
            "range", "repeat", "break", "continue"
        ],
        "sequence": [
            "list", "lists", "tuple", "tuples", "index", "indexes", "indexing",
            "slice", "slicing", "element", "elements", "append", "item", "items",
            "order", "sequence", "sequences", "op_lbracket", "op_rbracket"
        ],
        "function": [
            "def", "call", "calling", "parameter", "parameters", "argument",
            "arguments", "return", "returns", "returning", "scope", "output"
        ],
    }

    def __init__(self, dimension: int = 256):
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return "deterministic_semantic"

    def _tokenize(self, text: str) -> List[str]:
        # Preserve significant code operators as distinct semantic tokens
        text = text.replace("==", " op_equals ")
        text = text.replace("!=", " op_notequals ")
        text = text.replace("//", " op_floordiv ")
        text = text.replace("=", " op_assign ")
        text = text.replace("+", " op_add ")
        text = text.replace("-", " op_sub ")
        text = text.replace("*", " op_mul ")
        text = text.replace("/", " op_div ")
        text = text.replace("%", " op_mod ")
        text = text.replace("[", " op_lbracket ")
        text = text.replace("]", " op_rbracket ")
        raw = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        filtered = [t for t in raw if t not in self.STOPWORDS]
        return filtered if filtered else raw

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dim

        vec = [0.0] * self._dim
        tokens = self._tokenize(text)

        for tok in tokens:
            # Word-level hash with Murmur-style SHA256 sign projection
            h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign * 2.0

            # Subword character n-grams (3 and 4-grams) for morphological robustness
            for n in (3, 4):
                if len(tok) >= n:
                    for i in range(len(tok) - n + 1):
                        gram = tok[i:i + n]
                        gh = int(hashlib.sha256(gram.encode("utf-8")).hexdigest(), 16)
                        gidx = gh % self._dim
                        gsign = 1.0 if ((gh >> 8) & 1) else -1.0
                        vec[gidx] += gsign * 0.6

            # Semantic domain concept affinity
            for category, related_terms in self.SEMANTIC_ANCHORS.items():
                if tok == category or tok in related_terms:
                    ch = int(hashlib.sha256(f"anchor_{category}".encode("utf-8")).hexdigest(), 16)
                    cidx = ch % self._dim
                    csign = 1.0 if ((ch >> 8) & 1) else -1.0
                    vec[cidx] += csign * 2.2

        return normalize_vector(vec)


class GeminiEmbeddingService(BaseEmbeddingService):
    """Embeddings via Google Gemini API (text-embedding-004)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-004"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self._dim = 768

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return "gemini_api"

    def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:embedContent?key={self.api_key}"
        )
        payload = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": text}]}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                values = result.get("embedding", {}).get("values", [])
                return normalize_vector(values)
        except Exception as exc:
            raise RuntimeError(f"Gemini embedding API call failed: {exc}") from exc


class OpenAIEmbeddingService(BaseEmbeddingService):
    """Embeddings via OpenAI API (text-embedding-3-small)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self._dim = 1536

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def provider_name(self) -> str:
        return "openai_api"

    def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        url = "https://api.openai.com/v1/embeddings"
        payload = {"input": text, "model": self.model}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                values = result["data"][0]["embedding"]
                return normalize_vector(values)
        except Exception as exc:
            raise RuntimeError(f"OpenAI embedding API call failed: {exc}") from exc


def get_default_embedding_service(
    provider: Optional[str] = None, dimension: int = 128
) -> BaseEmbeddingService:
    """Factory to acquire the active embedding service with graceful offline fallback."""
    provider = provider or os.environ.get("TUTOR_EMBEDDING_PROVIDER")
    if provider == "gemini" and os.environ.get("GEMINI_API_KEY"):
        return GeminiEmbeddingService()
    if provider == "openai" and os.environ.get("OPENAI_API_KEY"):
        return OpenAIEmbeddingService()
    return DeterministicSemanticEmbedding(dimension=dimension)
