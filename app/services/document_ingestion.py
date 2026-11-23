"""
Document Ingestion Service:
Extracts and semantically chunks technical documents (Markdown, PDF, Plaintext)
into logical units based on document headings and structural hierarchy
rather than arbitrary character counts.
"""
from hashlib import sha256
from pathlib import Path
import re
from typing import List, Dict, Tuple, Optional, Any, Union

from app.models.rag import DocumentChunk, IngestionSummary

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class DocumentIngestionService:
    """Ingests Markdown and PDF educational documents using semantic heading-based chunking."""

    def __init__(self, min_chunk_words: int = 15):
        self.min_chunk_words = min_chunk_words

    def ingest_file(self, file_path: Union[str, Path]) -> Tuple[List[DocumentChunk], IngestionSummary]:
        """Ingest a file by auto-detecting format from extension."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {path}")

        ext = path.suffix.lower()
        if ext in (".md", ".markdown"):
            chunks = self.ingest_markdown_file(path)
            fmt = "markdown"
        elif ext == ".pdf":
            chunks = self.ingest_pdf_file(path)
            fmt = "pdf"
        elif ext in (".txt", ".text"):
            chunks = self.ingest_text_file(path)
            fmt = "text"
        else:
            # Default to markdown-style heading parsing
            chunks = self.ingest_markdown_file(path)
            fmt = "markdown"

        total_words = sum(c.word_count for c in chunks)
        unique_headings = []
        for c in chunks:
            if c.heading_path:
                h_str = " > ".join(c.heading_path)
                if h_str not in unique_headings:
                    unique_headings.append(h_str)

        summary = IngestionSummary(
            source_file=path.name,
            format=fmt,
            total_chunks=len(chunks),
            linked_chunks=sum(1 for c in chunks if c.concept_id),
            unlinked_chunks=sum(1 for c in chunks if not c.concept_id),
            heading_hierarchy=unique_headings,
            total_words=total_words,
        )
        return chunks, summary

    def ingest_markdown_text(
        self,
        text: str,
        source_name: str = "document.md",
    ) -> List[DocumentChunk]:
        """Semantically chunk Markdown text into logical units based on heading hierarchy."""
        lines = text.splitlines()
        chunks: List[DocumentChunk] = []
        doc_slug = self._slugify(Path(source_name).stem)

        heading_stack: List[Tuple[int, str]] = []  # (depth, title)
        current_lines: List[str] = []
        in_code_block = False
        chunk_index = 1

        heading_regex = re.compile(r"^(#{1,6})\s+(.+)$")

        def flush_current_chunk():
            nonlocal chunk_index, current_lines
            content = "\n".join(current_lines).strip()
            if not content:
                current_lines = []
                return

            words = len(content.split())
            if words < self.min_chunk_words and chunks:
                # Append short trailing blurbs to preceding chunk if reasonable
                prev = chunks[-1]
                prev.content = prev.content + "\n\n" + content
                prev.word_count = len(prev.content.split())
                current_lines = []
                return

            h_path = [title for _, title in heading_stack] if heading_stack else ["Introduction"]
            h_level = heading_stack[-1][0] if heading_stack else 1
            chunk_id = f"doc_{doc_slug}_{chunk_index:03d}"

            chunk = DocumentChunk(
                id=chunk_id,
                source=source_name,
                heading_path=h_path,
                heading_level=h_level,
                content=content,
                word_count=words,
                metadata={"format": "markdown", "chunk_index": chunk_index},
            )
            chunks.append(chunk)
            chunk_index += 1
            current_lines = []

        for line in lines:
            stripped = line.strip()
            # Toggle code block state so headers inside code aren't matched
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                current_lines.append(line)
                continue

            if in_code_block:
                current_lines.append(line)
                continue

            match = heading_regex.match(line)
            if match:
                # Found a heading outside code blocks!
                # Flush existing content before changing headings
                flush_current_chunk()

                hashes, title = match.groups()
                depth = len(hashes)
                clean_title = title.strip()

                # Pop headings of equal or deeper depth to maintain proper breadcrumbs
                while heading_stack and heading_stack[-1][0] >= depth:
                    heading_stack.pop()
                heading_stack.append((depth, clean_title))
            else:
                current_lines.append(line)

        # Flush any remaining content
        flush_current_chunk()
        return chunks

    def ingest_markdown_file(self, file_path: Path) -> List[DocumentChunk]:
        """Read and chunk a markdown file."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return self.ingest_markdown_text(text, source_name=file_path.name)

    def ingest_pdf_file(self, file_path: Path) -> List[DocumentChunk]:
        """Extract and semantically chunk a PDF file using section headings and page flow."""
        if not HAS_PYPDF:
            raise ImportError(
                "pypdf is required for PDF ingestion. Install with 'pip install pypdf'."
            )

        reader = pypdf.PdfReader(str(file_path))
        doc_slug = self._slugify(file_path.stem)
        chunks: List[DocumentChunk] = []

        # Common technical heading patterns in textbooks and lecture notes
        heading_pattern = re.compile(
            r"^(?:(?:chapter|section|\d+\.?\d*)\s+)?([A-Z0-9][A-Za-z0-9\s\-_:]{3,60})$"
        )

        current_heading = "Overview"
        current_lines: List[str] = []
        current_page = 1
        chunk_index = 1

        def flush_pdf_chunk(page_num: int):
            nonlocal chunk_index, current_lines, current_heading
            content = "\n".join(current_lines).strip()
            if not content:
                current_lines = []
                return

            words = len(content.split())
            if words < self.min_chunk_words and chunks:
                chunks[-1].content += "\n\n" + content
                chunks[-1].word_count = len(chunks[-1].content.split())
                current_lines = []
                return

            chunk_id = f"doc_{doc_slug}_{chunk_index:03d}"
            chunk = DocumentChunk(
                id=chunk_id,
                source=file_path.name,
                heading_path=[current_heading],
                heading_level=1,
                content=content,
                word_count=words,
                page_number=page_num,
                metadata={"format": "pdf", "page_number": page_num, "chunk_index": chunk_index},
            )
            chunks.append(chunk)
            chunk_index += 1
            current_lines = []

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_lines = page_text.splitlines()

            for line in page_lines:
                stripped = line.strip()
                if not stripped:
                    continue

                # Check if this line looks like a major section heading
                is_heading = (
                    stripped.isupper() and 4 <= len(stripped) <= 60
                ) or (
                    heading_pattern.match(stripped) and len(stripped.split()) <= 8
                )

                if is_heading and len(current_lines) > 3:
                    flush_pdf_chunk(page_idx + 1)
                    current_heading = stripped
                    current_page = page_idx + 1
                else:
                    current_lines.append(stripped)

        flush_pdf_chunk(current_page)
        return chunks

    def ingest_text_file(self, file_path: Path) -> List[DocumentChunk]:
        """Ingest plaintext file with paragraph and delimiter semantic chunking."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return self.ingest_markdown_text(text, source_name=file_path.name)

    @staticmethod
    def _slugify(name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_")
        return clean or "doc"
