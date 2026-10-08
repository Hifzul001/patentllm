from patentllm.ingestion.parsers import parse_jsonl
from patentllm.rag.chunking import chunk_corpus

def test_chunking_creates_claim_and_abstract_chunks():
    records = parse_jsonl("data/sample/sample_patents.jsonl")
    chunks = chunk_corpus(records)
    sections = {c.section for c in chunks}
    assert "abstract" in sections
    assert "claim" in sections
    assert len(chunks) >= len(records)
