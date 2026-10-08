from __future__ import annotations
from datetime import datetime
from patentllm.config import get_settings
from patentllm.ingestion.parsers import load_records
from patentllm.llm.fallback import deterministic_report
from patentllm.llm.ollama_client import OllamaClient
from patentllm.prompts import build_report_prompt
from patentllm.rag.chunking import chunk_corpus
from patentllm.rag.vector_store import TfidfPatentIndex
from patentllm.schemas import Audience, PatentReport, ReportRequest, ReportSection
from patentllm.storage import load_patents, save_report, upsert_patents
from patentllm.utils import stable_hash

def ingest_files(paths: list[str]) -> int:
    records = load_records(paths)
    return upsert_patents(records)

def build_index(index_path: str | None = None) -> int:
    settings = get_settings()
    records = load_patents()
    chunks = chunk_corpus(records)
    TfidfPatentIndex().build(chunks).save(index_path or settings.index_path)
    return len(chunks)

def _load_or_build_index(index_path: str | None = None) -> TfidfPatentIndex:
    settings = get_settings()
    path = index_path or settings.index_path
    try:
        return TfidfPatentIndex.load(path)
    except FileNotFoundError:
        build_index(path)
        return TfidfPatentIndex.load(path)

def _parse_markdown_sections(markdown: str) -> tuple[str, list[ReportSection]]:
    sections: list[ReportSection] = []
    current_heading = "Report"
    buffer: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if buffer:
                sections.append(ReportSection(heading=current_heading, content="\n".join(buffer).strip()))
                buffer = []
            current_heading = line.replace("## ", "").strip()
        elif not line.startswith("# "):
            buffer.append(line)
    if buffer:
        sections.append(ReportSection(heading=current_heading, content="\n".join(buffer).strip()))
    executive = next((s.content for s in sections if "executive" in s.heading.lower()), sections[0].content[:1000] if sections else "")
    return executive, sections

def generate_report(request: ReportRequest, save: bool = True) -> PatentReport:
    settings = get_settings()
    model = request.model or settings.default_model
    index = _load_or_build_index(settings.index_path)
    evidence = index.search(request.query, top_k=request.top_k)
    prompt = build_report_prompt(request.query, request.audience, evidence)
    try:
        llm_response = OllamaClient(settings.ollama_base_url).generate(prompt=prompt, model=model)
    except Exception:
        llm_response = deterministic_report(
            query=request.query, audience=request.audience, evidence=evidence,
            model_name=f"{model} unavailable; deterministic-fallback",
        )
    executive_summary, sections = _parse_markdown_sections(llm_response.text)
    report = PatentReport(
        report_id=stable_hash(request.query, request.audience.value, datetime.utcnow().isoformat()),
        query=request.query, audience=request.audience, model=llm_response.model,
        generated_at=datetime.utcnow(), executive_summary=executive_summary,
        sections=sections, evidence=evidence,
        limitations=[
            "Generated reports summarize retrieved public patent text and are not legal advice.",
            "Patent family status, claim scope, and freedom-to-operate require expert review.",
        ],
        metadata={"latency_seconds": llm_response.latency_seconds, "used_fallback": llm_response.used_fallback, "top_k": request.top_k},
    )
    if save:
        save_report(report)
    return report

def load_demo_corpus() -> int:
    return ingest_files(["data/sample/sample_patents.jsonl"])

def run_demo() -> PatentReport:
    load_demo_corpus()
    build_index()
    return generate_report(ReportRequest(query="battery thermal management systems for electric vehicles", audience=Audience.rd, top_k=5))
