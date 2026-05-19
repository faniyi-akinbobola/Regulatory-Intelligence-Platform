import re
from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.parsers import ParsedDocument, ParsedPage


@dataclass
class DocumentChunk:
    text: str
    document_name: str
    page_number: int          # from parser, 1-based
    section_number: str       # e.g. "23", "15.2", "Rule 7"
    section_title: str        # e.g. "Licensing Requirements"
    hierarchy: list[str]      # e.g. ["PART II", "CHAPTER 3", "Section 15"]
    chunk_index: int          # position within the document
    metadata: dict = field(default_factory=dict)


# Regex patterns ordered from broad (Part/Chapter) to narrow (subsections)
SECTION_PATTERNS = [
    # PART I / PART II / PART ONE
    r"^(PART\s+(?:[IVX]+|\d+|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN))\s*[:\-–]?\s*(.*)$",
    # CHAPTER 1 / CHAPTER THREE
    r"^(CHAPTER\s+(?:[IVX]+|\d+|ONE|TWO|THREE|FOUR|FIVE))\s*[:\-–]?\s*(.*)$",
    # Section 23 / Section 23. / SECTION 23
    r"^((?:Section|SECTION|Regulation|REGULATION|Rule|RULE)\s+\d+(?:\.\d+)*)\s*[:\-–\.]?\s*(.*)$",
    # Numbered sections: 1. / 1.1 / 15.2.3
    r"^(\d+(?:\.\d+)+)\s+([A-Z][^a-z]{5,})$",  # e.g. "3.2 LICENSING REQUIREMENTS"
]

_COMPILED_PATTERNS = [re.compile(p, re.MULTILINE) for p in SECTION_PATTERNS]

MAX_CHUNK_SIZE = 1000   # tokens approximate (~4 chars/token → 4000 chars)
CHUNK_OVERLAP = 100


def _detect_section_header(line: str) -> tuple[str, str] | None:
    """Returns (section_number, section_title) if the line is a section header."""
    line = line.strip()
    for pattern in _COMPILED_PATTERNS:
        match = pattern.match(line)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return None


def _build_hierarchy(breadcrumbs: list[tuple[str, str]]) -> list[str]:
    """Converts breadcrumb stack into a readable hierarchy list."""
    return [f"{num} {title}".strip() for num, title in breadcrumbs]


def _split_oversized(text: str) -> list[str]:
    """Fallback: split a section that exceeds MAX_CHUNK_SIZE."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_SIZE * 4,   # chars, ~MAX_CHUNK_SIZE tokens
        chunk_overlap=CHUNK_OVERLAP * 4,
        separators=["\n\n", "\n", ". ", " "],
    )
    return splitter.split_text(text)


def chunk_document(doc: ParsedDocument) -> list[DocumentChunk]:
    """
    Chunks a ParsedDocument into semantically meaningful legal chunks.
    Preserves section numbers, hierarchy, and page references.
    """
    chunks: list[DocumentChunk] = []
    chunk_index = 0

    # Track current section context
    current_section_number = "preamble"
    current_section_title = ""
    current_page = 1
    current_text_lines: list[str] = []
    breadcrumbs: list[tuple[str, str]] = []  # stack of (section_num, title)

    def flush(page: int):
        """Emit the accumulated text as one or more chunks."""
        nonlocal chunk_index
        text = "\n".join(current_text_lines).strip()
        if not text:
            return

        segments = (
            _split_oversized(text)
            if len(text) > MAX_CHUNK_SIZE * 4
            else [text]
        )

        for segment in segments:
            chunks.append(DocumentChunk(
                text=segment,
                document_name=doc.file_name,
                page_number=page,
                section_number=current_section_number,
                section_title=current_section_title,
                hierarchy=_build_hierarchy(breadcrumbs),
                chunk_index=chunk_index,
                metadata={
                    "source": doc.file_name,
                    "page": page,
                    "section": current_section_number,
                    "title": current_section_title,
                },
            ))
            chunk_index += 1

    for page in doc.pages:
        current_page = page.page_number
        lines = page.text.splitlines()

        for line in lines:
            header = _detect_section_header(line)
            if header:
                # Flush previous section before starting new one
                flush(current_page)
                current_text_lines = []

                section_num, section_title = header
                current_section_number = section_num
                current_section_title = section_title

                # Update breadcrumb hierarchy
                # PART/CHAPTER reset deeper levels; Section/Rule add to stack
                upper = section_num.upper()
                if upper.startswith("PART"):
                    breadcrumbs = [(section_num, section_title)]
                elif upper.startswith("CHAPTER"):
                    breadcrumbs = [b for b in breadcrumbs if b[0].upper().startswith("PART")]
                    breadcrumbs.append((section_num, section_title))
                else:
                    breadcrumbs = [b for b in breadcrumbs if b[0].upper().startswith(("PART", "CHAPTER"))]
                    breadcrumbs.append((section_num, section_title))

            current_text_lines.append(line)

    # Flush final section
    flush(current_page)
    return chunks


# example outcome:
# DocumentChunk(
#     text="A bank shall not carry on banking business in Nigeria...",
#     document_name="BOFIA.pdf",
#     page_number=14,
#     section_number="Section 9",
#     section_title="Prohibition on unlicensed banking",
#     hierarchy=["PART II", "CHAPTER 1 LICENSING", "Section 9"],
#     chunk_index=22,
#     metadata={"source": "BOFIA.pdf", "page": 14, "section": "Section 9", ...}
# )