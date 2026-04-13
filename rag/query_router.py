"""Cross-company RAG query router. Implementation lands in RAG enablement phase."""


def query(question: str, ticker_filter: list[str] | None = None) -> list[dict]:
    raise NotImplementedError("RAG is disabled until embeddings are enabled.")
