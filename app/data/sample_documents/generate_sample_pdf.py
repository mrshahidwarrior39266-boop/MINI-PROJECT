"""Utility script to generate sample PDF files for testing and demonstration."""
from pathlib import Path


def create_sample_pdf(output_path: Path) -> Path:
    """Generate a clean, strictly compliant multi-section PDF document for ingestion testing."""
    body = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"5 0 obj << /Length 380 >> stream\n"
        b"BT\n"
        b"/F1 16 Tf\n"
        b"50 720 Td\n"
        b"(SECTION 1: FUNCTION DEFINITIONS AND CALL STACKS) Tj\n"
        b"/F1 12 Tf\n"
        b"0 -30 Td\n"
        b"(Functions in Python are defined with the def keyword. Parameters act as local variable bindings) Tj\n"
        b"0 -20 Td\n"
        b"(within the function call frame. When the function returns, its local stack frame is dismantled.) Tj\n"
        b"0 -40 Td\n"
        b"/F1 16 Tf\n"
        b"(SECTION 2: RETURN VALUES AND SCOPE ISOLATION) Tj\n"
        b"/F1 12 Tf\n"
        b"0 -30 Td\n"
        b"(A function without an explicit return statement implicitly returns None. Variables assigned inside) Tj\n"
        b"0 -20 Td\n"
        b"(the function body reside in local scope and do not leak into the surrounding global environment.) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
    )

    # Calculate exact byte offsets for the cross-reference table
    offsets = [0]
    for obj_id in [b"1 0 obj", b"2 0 obj", b"3 0 obj", b"4 0 obj", b"5 0 obj"]:
        offsets.append(body.find(obj_id))

    xref_pos = len(body)
    xref_table = "xref\n0 6\n0000000000 65535 f \n"
    for off in offsets[1:]:
        xref_table += f"{off:010d} 00000 n \n"
    trailer = f"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"

    full_pdf = body + xref_table.encode("ascii") + trailer.encode("ascii")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(full_pdf)
    return output_path


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "python_functions_reference.pdf"
    create_sample_pdf(out)
    print(f"Generated clean sample PDF at: {out}")
