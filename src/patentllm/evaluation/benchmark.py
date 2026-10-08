from __future__ import annotations
import pandas as pd
from patentllm.pipeline import generate_report
from patentllm.schemas import Audience, ReportRequest

def benchmark_models(models: list[str], query: str, audience: Audience, top_k: int = 5) -> pd.DataFrame:
    rows = []
    for model in models:
        report = generate_report(ReportRequest(query=query, audience=audience, top_k=top_k, model=model), save=False)
        rows.append({
            "model": report.model,
            "query": query,
            "audience": audience.value,
            "latency_seconds": report.metadata.get("latency_seconds"),
            "used_fallback": report.metadata.get("used_fallback"),
            "evidence_items": len(report.evidence),
            "sections": len(report.sections),
            "summary_chars": len(report.executive_summary),
        })
    return pd.DataFrame(rows)
