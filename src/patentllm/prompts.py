from __future__ import annotations
from patentllm.schemas import Audience, EvidenceItem

AUDIENCE_PERSONAS = {
    Audience.rd: "You are a senior patent intelligence analyst supporting an R&D team. Focus on technical mechanisms, claim patterns, design alternatives, novelty signals, and open engineering questions.",
    Audience.sales: "You are a competitive-intelligence analyst supporting a B2B sales team. Translate patent evidence into competitor positioning, customer-relevant implications, and objection-handling notes.",
    Audience.marketing: "You are an innovation marketing strategist. Convert patent evidence into clear messaging angles, market narratives, and proof points without exaggeration.",
    Audience.executive: "You are an executive strategy analyst. Summarize portfolio-level implications, risks, opportunities, and recommended next steps.",
}

REPORT_SCHEMAS = {
    Audience.rd: ["Executive summary", "Technology landscape", "Key claim patterns", "Technical differentiation", "Whitespace opportunities", "Risks and uncertainties", "Recommended R&D next steps"],
    Audience.sales: ["Executive summary", "Competitor positioning", "Customer-facing implications", "Differentiation opportunities", "Likely objections", "Sales enablement talking points"],
    Audience.marketing: ["Executive summary", "Innovation narrative", "Messaging angles", "Proof points from patents", "Claims to avoid overstating", "Recommended campaign themes"],
    Audience.executive: ["Executive summary", "Portfolio signal", "Strategic opportunities", "Competitive risks", "Investment implications", "Recommended next steps"],
}

def format_evidence(evidence: list[EvidenceItem]) -> str:
    return "\n\n".join(
        f"[E{i}] patent_id={item.patent_id}; section={item.section}; score={item.score:.3f}\n{item.text}"
        for i, item in enumerate(evidence, start=1)
    )

def build_report_prompt(query: str, audience: Audience, evidence: list[EvidenceItem]) -> str:
    sections = "\n".join(f"- {s}" for s in REPORT_SCHEMAS[audience])
    return f'''{AUDIENCE_PERSONAS[audience]}

Task:
Generate a structured patent intelligence report for the query:
"{query}"

Required report sections:
{sections}

Grounding rules:
- Use only the patent evidence below.
- Cite patent IDs inline whenever making a factual statement.
- Separate evidence from inference.
- If evidence is insufficient, say so explicitly.
- Do not provide legal advice, freedom-to-operate conclusions, infringement claims, or patentability opinions.
- Keep the report practical for the target business function.

Patent evidence:
{format_evidence(evidence)}

Return the report in clear Markdown.'''.strip()
