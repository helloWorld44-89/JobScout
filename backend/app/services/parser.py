from io import BytesIO


def extract_resume_text(content: bytes, filename: str) -> str:
    """Extract plain text from a PDF, DOCX, or plain-text file."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        import pypdf  # type: ignore[import-untyped]

        reader = pypdf.PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if lower.endswith(".docx"):
        import docx  # type: ignore[import-untyped]

        doc = docx.Document(BytesIO(content))
        return "\n".join(para.text for para in doc.paragraphs)
    return content.decode("utf-8", errors="replace")
