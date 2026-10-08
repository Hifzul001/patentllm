from patentllm.ingestion.parsers import parse_jsonl

def test_parse_sample_patents():
    records = parse_jsonl("data/sample/sample_patents.jsonl")
    assert len(records) == 5
    assert records[0].patent_id == "US-2026-000001-A1"
    assert "Battery" in records[0].title
