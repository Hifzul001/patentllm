from __future__ import annotations
import time
from collections import Counter
from patentllm.llm.ollama_client import LLMResponse
from patentllm.prompts import REPORT_SCHEMAS
from patentllm.schemas import Audience, EvidenceItem

def _top_terms(text: str, limit: int = 8) -> list[str]:
    words = [w.lower().strip(".,;:()[]") for w in text.split() if len(w) > 5 and w.lower() not in {"patent", "system", "method", "wherein", "comprising"}]
    return [w for w, _ in Counter(words).most_common(limit)]

def deterministic_report(query: str, audience: Audience, evidence: list[EvidenceItem], model_name: str = "deterministic-fallback") -> LLMResponse:
    started = time.perf_counter()
    joined = " ".join(item.text for item in evidence)
    terms = ", ".join(_top_terms(joined)) or "no dominant technical terms found"
    patent_ids = sorted({item.patent_id for item in evidence})
    sections = []
    for section in REPORT_SCHEMAS[audience]:
        if section == "Executive summary":
            body = f"The retrieved evidence for '{query}' covers {len(patent_ids)} patent(s): {', '.join(patent_ids)}. Dominant terms include {terms}. This fallback report is deterministic and should be replaced by an Ollama-generated report for richer analysis."
        elif "risk" in section.lower() or "uncert" in section.lower() or "avoid" in section.lower():
            body = "The evidence should be reviewed by a patent or domain expert before legal, freedom-to-operate, filing, or investment decisions. This system summarizes public text and does not provide legal advice."
        elif "next" in section.lower() or "recommended" in section.lower():
            body = "Recommended next step: review the highest-scoring claim passages, validate assignee and family metadata, and compare retrieved patents against internal product or R&D roadmaps."
        else:
            bullets = [f"- {item.patent_id} / {item.section}: {item.text[:260]}..." for item in evidence[:3]]
            body = "\n".join(bullets) if bullets else "No evidence was retrieved."
        sections.append(f"## {section}\n{body}")
    text = f"# PatentLLM Report: {query}\n\n" + "\n\n".join(sections)
    return LLMResponse(text=text, model=model_name, latency_seconds=time.perf_counter() - started, used_fallback=True)
