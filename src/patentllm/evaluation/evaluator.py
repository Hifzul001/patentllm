from __future__ import annotations
import json, time
from pathlib import Path
import pandas as pd
from patentllm.pipeline import generate_report
from patentllm.schemas import EvaluationExample, EvaluationResult, ReportRequest

def _contains_rate(text: str, terms: list[str]) -> float:
    if not terms:
        return 1.0
    lower = text.lower()
    return sum(1 for t in terms if t.lower() in lower) / len(terms)

def evaluate_example(example: EvaluationExample, model: str | None = None) -> EvaluationResult:
    started = time.perf_counter()
    report = generate_report(ReportRequest(query=example.query, audience=example.audience, model=model), save=False)
    report_text = " ".join([report.executive_summary] + [s.content for s in report.sections])
    evidence_patent_ids = {e.patent_id for e in report.evidence}
    expected_patents = set(example.expected_patent_ids)
    evidence_coverage = len(expected_patents & evidence_patent_ids) / len(expected_patents) if expected_patents else min(1.0, len(evidence_patent_ids) / max(1, len(report.evidence)))
    expected_term_recall = _contains_rate(report_text, example.expected_terms)
    forbidden_term_rate = 1.0 - _contains_rate(report_text, example.forbidden_terms)
    hallucination_risk = max(0.0, 1.0 - ((evidence_coverage + expected_term_recall + forbidden_term_rate) / 3))
    return EvaluationResult(
        query=example.query, audience=example.audience, model=report.model,
        evidence_coverage=evidence_coverage, expected_term_recall=expected_term_recall,
        forbidden_term_rate=forbidden_term_rate, hallucination_risk=hallucination_risk,
        latency_seconds=time.perf_counter() - started,
        notes="Heuristic evaluator for portfolio demos; replace with human labels or LLM-as-judge for production.",
    )

def load_labelled(path: str | Path) -> list[EvaluationExample]:
    examples = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                examples.append(EvaluationExample.model_validate(json.loads(line)))
    return examples

def evaluate_file(path: str | Path, model: str | None = None, output: str | Path | None = None) -> pd.DataFrame:
    df = pd.DataFrame([evaluate_example(example, model=model).model_dump() for example in load_labelled(path)])
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False)
    return df
