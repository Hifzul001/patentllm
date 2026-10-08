from __future__ import annotations
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from patentllm.schemas import EvidenceItem, PatentChunk
from patentllm.utils import ensure_parent

class TfidfPatentIndex:
    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1, max_features=50000)
        self.chunks: list[PatentChunk] = []
        self.matrix = None

    def build(self, chunks: list[PatentChunk]) -> "TfidfPatentIndex":
        self.chunks = chunks
        docs = [f"{c.section} {c.metadata.get('title', '')} {c.text}" for c in chunks]
        self.matrix = self.vectorizer.fit_transform(docs)
        return self

    def search(self, query: str, top_k: int = 5) -> list[EvidenceItem]:
        if self.matrix is None or not self.chunks:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).ravel()
        ranked = scores.argsort()[::-1][:top_k]
        return [
            EvidenceItem(
                patent_id=self.chunks[int(i)].patent_id,
                section=self.chunks[int(i)].section,
                text=self.chunks[int(i)].text,
                score=float(scores[int(i)]),
                source_url=self.chunks[int(i)].metadata.get("source_url"),
            )
            for i in ranked
        ]

    def save(self, path: str | Path) -> None:
        p = ensure_parent(path)
        with p.open("wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "TfidfPatentIndex":
        with Path(path).open("rb") as f:
            return pickle.load(f)
