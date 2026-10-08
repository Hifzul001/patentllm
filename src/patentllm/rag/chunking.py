from __future__ import annotations
import re
from patentllm.schemas import PatentChunk, PatentRecord
from patentllm.utils import clean_text, stable_hash

def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) * 4 // 3)

def split_claims(claims: str) -> list[str]:
    claims = clean_text(claims)
    if not claims:
        return []
    parts = re.split(r"(?=(?:^|\s)(?:\d{1,3})\.\s)", claims)
    clean_parts = [clean_text(p) for p in parts if len(clean_text(p)) > 30]
    return clean_parts or [claims]

def sliding_chunks(text: str, max_words: int = 180, overlap: int = 35) -> list[str]:
    words = clean_text(text).split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks

def chunk_patent(record: PatentRecord) -> list[PatentChunk]:
    chunks: list[PatentChunk] = []
    def add(section: str, text: str, index: int = 0):
        text_clean = clean_text(text)
        if not text_clean:
            return
        chunk_id = stable_hash(record.patent_id, section, str(index), text_clean[:80])
        chunks.append(PatentChunk(
            chunk_id=chunk_id, patent_id=record.patent_id, section=section, text=text_clean,
            token_estimate=estimate_tokens(text_clean),
            metadata={"title": record.title, "assignees": record.assignees, "cpc_codes": record.cpc_codes, "source_url": record.source_url},
        ))
    add("title", record.title)
    add("abstract", record.abstract)
    for i, claim in enumerate(split_claims(record.claims)):
        add("claim", claim, i)
    for i, chunk in enumerate(sliding_chunks(record.description)):
        add("description", chunk, i)
    add("metadata", " ".join([
        f"Assignees: {', '.join(record.assignees)}",
        f"Inventors: {', '.join(record.inventors)}",
        f"CPC: {', '.join(record.cpc_codes)}",
        f"IPC: {', '.join(record.ipc_codes)}",
    ]))
    return chunks

def chunk_corpus(records: list[PatentRecord]) -> list[PatentChunk]:
    chunks = []
    for record in records:
        chunks.extend(chunk_patent(record))
    return chunks
