from __future__ import annotations
import json, re
from pathlib import Path
from typing import Iterable
import pandas as pd
from pypdf import PdfReader
from patentllm.schemas import PatentRecord
from patentllm.utils import clean_text, split_list_field, stable_hash

FIELD_ALIASES = {
    "patent_id": ["patent_id", "publication_number", "publication", "pub_number", "id", "patent"],
    "title": ["title", "invention_title"],
    "abstract": ["abstract", "summary"],
    "claims": ["claims", "claim_text", "claim"],
    "description": ["description", "specification", "body"],
    "assignees": ["assignees", "assignee", "applicant", "applicants"],
    "inventors": ["inventors", "inventor"],
    "publication_date": ["publication_date", "pub_date", "date"],
    "filing_date": ["filing_date", "application_date"],
    "jurisdiction": ["jurisdiction", "country", "office"],
    "cpc_codes": ["cpc_codes", "cpc", "classifications"],
    "ipc_codes": ["ipc_codes", "ipc"],
    "source_url": ["source_url", "url", "link"],
}

def _value(row: dict, canonical: str) -> object:
    for key in FIELD_ALIASES[canonical]:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None

def normalise_row(row: dict) -> PatentRecord:
    row = {str(k).strip().lower(): v for k, v in row.items()}
    patent_id = clean_text(_value(row, "patent_id"))
    title = clean_text(_value(row, "title"))
    abstract = clean_text(_value(row, "abstract"))
    claims = clean_text(_value(row, "claims"))
    description = clean_text(_value(row, "description"))
    if not patent_id:
        patent_id = "AUTO-" + stable_hash(title, abstract, claims)
    return PatentRecord(
        patent_id=patent_id, title=title, abstract=abstract, claims=claims, description=description,
        assignees=split_list_field(_value(row, "assignees")),
        inventors=split_list_field(_value(row, "inventors")),
        publication_date=clean_text(_value(row, "publication_date")) or None,
        filing_date=clean_text(_value(row, "filing_date")) or None,
        jurisdiction=clean_text(_value(row, "jurisdiction")) or None,
        cpc_codes=split_list_field(_value(row, "cpc_codes")),
        ipc_codes=split_list_field(_value(row, "ipc_codes")),
        source_url=clean_text(_value(row, "source_url")) or None,
        metadata={k: v for k, v in row.items()},
    )

def parse_csv(path: str | Path) -> list[PatentRecord]:
    return [normalise_row(row) for row in pd.read_csv(path).to_dict(orient="records")]

def parse_jsonl(path: str | Path) -> list[PatentRecord]:
    records = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(normalise_row(json.loads(line)))
    return records

def parse_txt(path: str | Path) -> list[PatentRecord]:
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    return [PatentRecord(
        patent_id="TXT-" + stable_hash(str(path), text[:500]),
        title=Path(path).stem.replace("_", " ").title(), abstract=text[:1200],
        description=text
    )]

def parse_pdf(path: str | Path) -> list[PatentRecord]:
    reader = PdfReader(str(path))
    text = clean_text("\n".join(page.extract_text() or "" for page in reader.pages))
    return [PatentRecord(
        patent_id="PDF-" + stable_hash(str(path), text[:500]),
        title=Path(path).stem.replace("_", " ").title(), abstract=text[:1200],
        description=text, metadata={"pages": len(reader.pages)}
    )]

def load_records(paths: Iterable[str | Path]) -> list[PatentRecord]:
    records = []
    for path in paths:
        p = Path(path)
        suffix = p.suffix.lower()
        if suffix == ".csv":
            records.extend(parse_csv(p))
        elif suffix == ".jsonl":
            records.extend(parse_jsonl(p))
        elif suffix == ".json":
            rows = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(rows, dict):
                rows = [rows]
            records.extend(normalise_row(r) for r in rows)
        elif suffix == ".pdf":
            records.extend(parse_pdf(p))
        elif suffix in {".txt", ".md"}:
            records.extend(parse_txt(p))
        else:
            raise ValueError(f"Unsupported input type: {p}")
    return records
