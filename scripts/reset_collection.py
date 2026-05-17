"""
Reset the Qdrant regulations collection to add hybrid (dense + sparse) vector support.

WARNING: This permanently deletes all indexed data.
After running this script, re-ingest all documents via POST /regulations/upload.

Usage:
    uv run python scripts/reset_collection.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.qdrant import recreate_qdrant_collection
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def main():
    print(f"\nThis will DROP and RECREATE the '{settings.qdrant_collection_name}' collection.")
    print("All indexed documents will be lost and must be re-ingested.\n")
    confirm = input("Type 'yes' to continue: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    await recreate_qdrant_collection()
    print(
        f"\nCollection '{settings.qdrant_collection_name}' recreated with "
        "dense (768-dim cosine) + sparse (BM25) vectors.\n"
        "Re-ingest all documents via:\n"
        "  curl -X POST http://localhost:8000/regulations/upload -F 'file=@doc.pdf' "
        "-F 'regulator=CBN' -F 'document_type=Guideline'\n"
    )


if __name__ == "__main__":
    asyncio.run(main())
