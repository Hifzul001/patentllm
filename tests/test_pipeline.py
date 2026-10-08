from patentllm.pipeline import build_index, generate_report, ingest_files
from patentllm.schemas import Audience, ReportRequest

def test_generate_report_with_fallback(tmp_path, monkeypatch):
    db_path = tmp_path / "patentllm.db"
    index_path = tmp_path / "index.pkl"
    monkeypatch.setenv("PATENTLLM_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PATENTLLM_INDEX_PATH", str(index_path))
    monkeypatch.setenv("PATENTLLM_OLLAMA_BASE_URL", "http://127.0.0.1:9")
    ingest_files(["data/sample/sample_patents.jsonl"])
    build_index(str(index_path))
    report = generate_report(ReportRequest(query="battery thermal management", audience=Audience.rd, top_k=3, model="llama3.1:8b"), save=False)
    assert report.evidence
    assert report.sections
    assert "fallback" in report.model.lower()
