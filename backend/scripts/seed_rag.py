import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.rag.seed_pack import seed_starter_knowledge_pack


def main() -> int:
    get_settings.cache_clear()
    result = seed_starter_knowledge_pack()
    print("Starter RAG seed pack")
    print(f"entries attempted: {result.entries_attempted}")
    print(f"entries ingested: {result.entries_ingested}")
    print(f"duplicates skipped: {result.duplicates_skipped}")
    if result.skipped_titles:
        print("skipped titles:")
        for title in result.skipped_titles:
            print(f"- {title}")
    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
