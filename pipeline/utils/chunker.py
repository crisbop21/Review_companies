"""RAG-ready chunker. Implementation lands in Phase 5 Task 5.2.

Each pipeline step's output is decomposed into 50-200 word chunks with
standardized metadata. Chunks are deterministic and one-idea-per-chunk so
embeddings yield clean retrieval when RAG is enabled.
"""


def build_metadata(ticker: str, quarter: str, chunk_type: str, **extras) -> dict:
    raise NotImplementedError("Implemented in Phase 5 Task 5.2.")
