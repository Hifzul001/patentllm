from __future__ import annotations
import json
from pathlib import Path
from patentllm.schemas import PatentReport
from patentllm.utils import ensure_parent

def report_to_markdown(report: PatentReport) -> str:
    lines = [
        "# PatentLLM Report", "", f"**Query:** {report.query}", f"**Audience:** {report.audience.value}",
        f"**Model:** {report.model}", f"**Generated:** {report.generated_at.isoformat()}", "",
        "## Executive summary", report.executive_summary, "",
    ]
    for section in report.sections:
        lines.extend([f"## {section.heading}", section.content, ""])
    lines.append("## Evidence")
    for i, item in enumerate(report.evidence, start=1):
        lines.append(f"{i}. **{item.patent_id}** ({item.section}, score={item.score:.3f}) — {item.text[:300]}...")
    if report.limitations:
        lines.extend(["", "## Limitations"])
        lines.extend([f"- {x}" for x in report.limitations])
    return "\n".join(lines)

def save_report_files(report: PatentReport, output_dir: str | Path = "reports") -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = ensure_parent(out / f"{report.report_id}.md")
    json_path = ensure_parent(out / f"{report.report_id}.json")
    md_path.write_text(report_to_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    return md_path, json_path
