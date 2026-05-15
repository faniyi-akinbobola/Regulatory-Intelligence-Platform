import fitz
import logging
import pdfplumber
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    page_number: int
    text: str
    tables: list[list] = field(default_factory=list)
    has_table: bool = False

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
    """"Extract text from a page using pdfplumber, which is better at handling tables."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        return page.extract_text() or ""
    
def parse_document(pdf_path: str) -> ParsedDocument:
    """   
    Primary parser using PyMuPDF. Falls back to pdfplumber on pages with tables.
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

            if has_table:
                logger.debug("[PARSE] Page %d has tables — using pdfplumber", page_index + 1)
                text = _extract_page_with_pdfplumber(pdf_path, page_index)
            else:
                text = pymupdf_text

            if not text.strip():
                logger.debug("[PARSE] Page %d extracted no text — may be image/blank", page_index + 1)

            pages.append(ParsedPage(
                page_number=page_index + 1,  # 1-based for citations
                text=text.strip(),
                tables=tables,
                has_table=has_table,
            ))

    return ParsedDocument(
        file_name=Path(pdf_path).name,
        total_pages=total_pages,
        pages=pages,
    )