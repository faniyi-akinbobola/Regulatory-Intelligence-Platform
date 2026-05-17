def format_citation(chunk: dict) -> str:
    """
    Produces a human-readable citation string from a Qdrant chunk payload.
    Example: "CBN Consumer Protection Regulations, Part Six (Page 4)"
    """
    parts = []
    if chunk.get("source"):
        # Strip temp-file names — use title if available, else source
        name = chunk.get("title") or chunk.get("source")
        parts.append(name)
    if chunk.get("section"):
        parts.append(chunk["section"])
    if chunk.get("page"):
        parts.append(f"Page {chunk['page']}")
    if chunk.get("regulator"):
        parts.insert(0, chunk["regulator"])
    return " | ".join(parts) if parts else "Unknown source"


def build_citation_object(chunk: dict) -> dict:
    """
    Returns a structured citation dict passed to agent inputs and stored in audit records.
    """
    return {
        "citation_string": format_citation(chunk),
        "document": chunk.get("source", ""),
        "section": chunk.get("section", ""),
        "title": chunk.get("title", ""),
        "page": chunk.get("page"),
        "regulator": chunk.get("regulator", ""),
        "text_excerpt": chunk.get("text", "")[:300],
    }


def build_citations_from_chunks(chunks: list[dict]) -> list[dict]:
    """Builds a list of citation objects from retrieved chunks."""
    return [build_citation_object(c) for c in chunks]