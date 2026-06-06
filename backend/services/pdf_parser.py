import os
import fitz  # PyMuPDF
import google.generativeai as genai
from fastapi import HTTPException
from dotenv import load_dotenv
from backend.utils.validators import sanitize_text

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ---------------------------------------------------------------------------
# Primary Text Extraction (text-based PDFs)
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF file.

    Strategy:
    1. Try direct text extraction with PyMuPDF (fast, works for text-based PDFs)
    2. If no text found (scanned/image PDF), fall back to Gemini Vision OCR
       which renders each page as an image and asks Gemini to read it

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        Cleaned, sanitized text string ready for AI processing.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not open PDF. It may be corrupted or password-protected. ({str(e)})",
        )

    if doc.page_count == 0:
        raise HTTPException(status_code=400, detail="The PDF has no pages.")

    # Attempt 1 — direct text extraction
    extracted_pages = []
    for page_num in range(doc.page_count):
        try:
            page_text = doc[page_num].get_text("text")
            if page_text.strip():
                extracted_pages.append(page_text)
        except Exception:
            continue

    if extracted_pages:
        doc.close()
        raw_text = "\n\n".join(extracted_pages)
        clean_text = sanitize_text(raw_text)
        if len(clean_text) >= 50:
            return clean_text
        # Text found but too short — still try vision
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Attempt 2 — Gemini Vision OCR for scanned/image PDFs
    # Re-open doc fresh since we may have closed it above
    return _extract_text_via_vision(doc, pdf_bytes)


# ---------------------------------------------------------------------------
# Gemini Vision OCR Fallback (scanned / image PDFs)
# ---------------------------------------------------------------------------

def _extract_text_via_vision(doc: fitz.Document, pdf_bytes: bytes) -> str:
    """
    Use Gemini 2.5 Flash vision to OCR pages from a scanned PDF.
    Renders each page as a high-resolution PNG and asks Gemini to
    extract all visible text preserving structure.
    """
    page_count = doc.page_count
    page_images_bytes = []

    # Render up to 5 pages (enough for any resume)
    max_pages = min(page_count, 5)

    for page_num in range(max_pages):
        try:
            page = doc[page_num]
            # Render at 2x resolution for better OCR accuracy
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            page_images_bytes.append(pix.tobytes("png"))
        except Exception:
            continue

    doc.close()

    if not page_images_bytes:
        raise HTTPException(
            status_code=422,
            detail="Could not render PDF pages. Please use the Paste Text tab instead.",
        )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(temperature=0.1),
        )

        # Build content parts using the correct SDK format
        content_parts = []

        content_parts.append(
            "You are an OCR engine. Extract ALL text visible in these resume page images. "
            "Preserve the structure: name, contact info, work experience, education, skills, "
            "projects, certifications. Output plain text only — no markdown, no commentary."
        )

        for i, img_bytes in enumerate(page_images_bytes):
            content_parts.append(f"\nPage {i + 1}:\n")
            content_parts.append(
                genai.protos.Part(
                    inline_data=genai.protos.Blob(
                        mime_type="image/png",
                        data=img_bytes,
                    )
                )
            )

        response = model.generate_content(content_parts)
        extracted_text = response.text.strip()

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Vision OCR Error] {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=(
                f"Vision OCR failed: {str(e)[:200]}. "
                "Please use the Paste Text tab to paste your resume content directly."
            ),
        )

    clean_text = sanitize_text(extracted_text)

    if len(clean_text) < 50:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not read enough text from this PDF. "
                "Please use the Paste Text tab to paste your resume content directly."
            ),
        )

    return clean_text


# ---------------------------------------------------------------------------
# Metadata Helper
# ---------------------------------------------------------------------------

def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """Extract basic metadata from a PDF for logging purposes."""
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
