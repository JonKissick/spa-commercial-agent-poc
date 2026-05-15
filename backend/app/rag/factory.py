from app.config import Settings
from app.rag.local_index import LocalRAGIndex


def create_rag_index(settings: Settings) -> LocalRAGIndex:
    if settings.rag_provider.strip().lower() != "local":
        raise ValueError("Only RAG_PROVIDER=local is implemented in Stage 5C.")
    return LocalRAGIndex(settings.local_rag_dir)
