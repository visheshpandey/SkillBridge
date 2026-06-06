import fitz  # PyMuPDF
from fastapi import HTTPException
from backend.utils.validators import sanitize_text


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract and clean all text content from a PDF file.

    Uses PyMuPDF (fitz) for fast, accurate text extraction
    with layout preservation across all pages.

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        Cleaned, sanitized text string ready for AI processing.

    Raises:
        HTTPException 400 if the PDF is corrupted or unreadable.
        HTTPException 422 if the PDF contains no extractable text (e.g. scanned image).
    """
    try:
        # Open PDF from bytes (no temp file needed)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not open PDF. The file may be corrupted or password-protected. ({str(e)})",
        )

    if doc.page_count == 0:
        raise HTTPException(
            status_code=400,
            detail="The PDF has no pages.",
        )

    extracted_pages = []

    for page_num in range(doc.page_count):
        try:
            page = doc[page_num]
            # "text" mode preserves reading order and layout
            page_text = page.get_text("text")
            if page_text.strip():
                extracted_pages.append(page_text)
        except Exception:
            # Skip unreadable pages, don't fail entire document
            continue

    doc.close()

    if not extracted_pages:
        raise HTTPException(
            status_code=422,
            detail=(
                "No text could be extracted from this PDF. "
                "If it is a scanned document, please use a PDF with selectable text."
            ),
        )

    # Join all pages and sanitize
    raw_text = "\n\n".join(extracted_pages)
    clean_text = sanitize_text(raw_text)

    if len(clean_text) < 50:
        raise HTTPException(
            status_code=422,
            detail="The extracted text is too short to analyze. Please upload a complete resume.",
        )

    return clean_text


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """
    Extract basic metadata from a PDF (page count, author, title).
    Used for logging and debugging purposes.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        metadata = {
            "page_count": doc.page_count,
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
        }
        doc.close()
        return metadata
    except Exception:
        return {"page_count": 0, "title": "", "author": ""}
