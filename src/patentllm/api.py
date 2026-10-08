from __future__ import annotations
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from patentllm.ingestion.parsers import load_records
from patentllm.pipeline import build_index, generate_report
from patentllm.schemas import PatentReport, ReportRequest
from patentllm.storage import get_report, load_patents, upsert_patents

app = FastAPI(
    title="PatentLLM API",
    description="Generate structured LLM reports from patent data using retrieval-augmented generation.",
    version="0.1.0",
)

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "patentllm"}

@app.get("/patents")
def list_patents() -> dict:
    patents = load_patents()
    return {"count": len(patents), "patents": [{"patent_id": p.patent_id, "title": p.title, "assignees": p.assignees, "publication_date": p.publication_date} for p in patents]}

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "upload.jsonl").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    records = load_records([tmp_path])
    count = upsert_patents(records)
    chunks = build_index()
    return {"ingested_patents": count, "indexed_chunks": chunks}

@app.post("/reports", response_model=PatentReport)
def create_report(request: ReportRequest) -> PatentReport:
    try:
        return generate_report(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.get("/reports/{report_id}", response_model=PatentReport)
def read_report(report_id: str) -> PatentReport:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.exception_handler(ValueError)
def value_error_handler(_, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
