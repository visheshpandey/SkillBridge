import os
from fastapi import HTTPException, UploadFile

# Maximum allowed file size: 10MB
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))

# PDF magic bytes — true PDF files always start with %PDF
PDF_MAGIC_BYTES = b"%PDF"


async def validate_pdf_upload(file: UploadFile) -> bytes:
    """
    Validate an uploaded file is a real PDF within size limits.

    Checks:
    - File extension is .pdf
    - MIME type is application/pdf
    - File is not empty
    - File does not exceed MAX_FILE_SIZE
    - First bytes match PDF magic bytes (prevents disguised files)

    Returns the raw file bytes if valid.
    Raises HTTPException with a human-readable message on failure.
    """

    # Check extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted. Please upload a .pdf file.",
        )

    # Check MIME type
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Expected application/pdf.",
        )

    # Read file contents
    contents = await file.read()

    # Check not empty
    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty. Please upload a valid PDF.",
        )

    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {max_mb:.0f}MB.",
        )

    # Check PDF magic bytes (prevents renamed non-PDF files)
    if not contents.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=400,
            detail="File does not appear to be a valid PDF. Magic bytes check failed.",
        )

    return contents


def sanitize_text(text: str) -> str:
    """
    Clean extracted resume text before sending to Gemini.

    - Removes null bytes that can break JSON encoding
    - Collapses excessive whitespace
    - Strips leading/trailing whitespace
    - Limits total length to prevent token overflow (approx 15k words)
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse runs of blank lines (more than 2 consecutive)
    import re
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Strip
    text = text.strip()

    # Cap at ~60,000 characters to stay well within Gemini token limits
    if len(text) > 60000:
        text = text[:60000] + "\n\n[Resume truncated due to length]"

    return text
