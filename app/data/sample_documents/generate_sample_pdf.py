"""Utility script to generate sample PDF files for testing and demonstration."""
import io
from pathlib import Path


def create_sample_pdf(output_path: Path) -> Path:
    """Generate a clean, valid multi-section PDF document for ingestion testing."""
    raw_pdf = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj
4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
5 0 obj << /Length 380 >> stream
BT
/F1 16 Tf
50 720 Td
(SECTION 1: FUNCTION DEFINITIONS AND CALL STACKS) Tj
/F1 12 Tf
0 -30 Td
(Functions in Python are defined with the def keyword. Parameters act as local variable bindings) Tj
0 -20 Td
(within the function call frame. When the function returns, its local stack frame is dismantled.) Tj
0 -40 Td
/F1 16 Tf
(SECTION 2: RETURN VALUES AND SCOPE ISOLATION) Tj
/F1 12 Tf
0 -30 Td
(A function without an explicit return statement implicitly returns None. Variables assigned inside) Tj
0 -20 Td
(the function body reside in local scope and do not leak into the surrounding global environment.) Tj
ET
endstream endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000318 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
750
%%EOF"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw_pdf)
    return output_path


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "python_functions_reference.pdf"
    create_sample_pdf(out)
    print(f"Generated sample PDF at: {out}")
