import fitz
import logging
import pdfplumber
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Minimum characters to consider a page as having usable text.
# Pages below this threshold are treated as image-based and sent to OCR.
_OCR_TEXT_THRESHOLD = 50


@dataclass
class ParsedPage:
    page_number: int
    text: str
    tables: list[list] = field(default_factory=list)
    has_table: bool = False
    ocr_used: bool = False


@dataclass
class ParsedDocument:
    file_name: str
    total_pages: int
    pages: list[ParsedPage]

    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())


def _has_tables(pdf_path: str, page_number: int) -> tuple[bool, list[list]]:
    """Check if a page has tables and extract them using pdfplumber."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        tables = page.extract_tables()
        return bool(tables), tables or []


def _extract_page_with_pdfplumber(pdf_path: str, page_number: int) -> str:
    """Extract text from a page using pdfplumber, which is better at handling tables."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        return page.extract_text() or ""


def _ocr_page(fitz_page: fitz.Page, page_number: int) -> str:
    """
    OCR fallback for image-based pages.
    Renders the page to a high-resolution image using PyMuPDF, then
    runs Tesseract to extract text. No extra dependencies beyond pytesseract.
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        # 2x zoom for better OCR accuracy (300 DPI equivalent)
        mat = fitz.Matrix(2.0, 2.0)
        pix = fitz_page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        text = pytesseract.image_to_string(image, lang="eng")
        logger.info("[PARSE] Page %d: OCR extracted %d chars", page_number, len(text))
        return text.strip()
    except ImportError:
        logger.warning(
            "[PARSE] Page %d: pytesseract not installed — cannot OCR image page", page_number
        )
        return ""
    except Exception as e:
        logger.warning("[PARSE] Page %d: OCR failed — %s", page_number, e)
        return ""


def parse_document(pdf_path: str) -> ParsedDocument:
    """
    Primary parser using PyMuPDF. Falls back to pdfplumber on pages with tables.
    Falls back to Tesseract OCR on pages with no extractable text (scanned/image PDFs).
    Returns a ParsedDocument with per-page text, metadata, and table data.
    """
    pdf_path = str(pdf_path)
    pages: list[ParsedPage] = []

    with fitz.open(pdf_path) as doc:
        total_pages = doc.page_count
        logger.debug("[PARSE] Opened %s — %d pages", Path(pdf_path).name, total_pages)

        for page_index in range(total_pages):
            page = doc[page_index]
            pymupdf_text = page.get_text("text")

            has_table, tables = _has_tables(pdf_path, page_index)
            ocr_used = False

            if has_table:
                logger.debug("[PARSE] Page %d has tables — using pdfplumber", page_index + 1)
                text = _extract_page_with_pdfplumber(pdf_path, page_index)
            else:
                text = pymupdf_text

            # OCR fallback: if both extractors returned very little text, the page is likely image-based
            if len(text.strip()) < _OCR_TEXT_THRESHOLD:
                logger.info(
                    "[PARSE] Page %d has minimal text (%d chars) — attempting OCR",
                    page_index + 1,
                    len(text.strip()),
                )
                ocr_text = _ocr_page(page, page_index + 1)
                if ocr_text:
                    text = ocr_text
                    ocr_used = True
                else:
                    logger.debug("[PARSE] Page %d: OCR returned no text — treating as blank", page_index + 1)

            pages.append(ParsedPage(
                page_number=page_index + 1,  # 1-based for citations
                text=text.strip(),
                tables=tables,
                has_table=has_table,
                ocr_used=ocr_used,
            ))

    return ParsedDocument(
        file_name=Path(pdf_path).name,
        total_pages=total_pages,
        pages=pages,
    )