from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
import requests
from bs4 import BeautifulSoup
from patentllm.schemas import PatentRecord
from patentllm.utils import clean_text, stable_hash

@dataclass
class SourceHint:
    name: str
    expected_format: str
    notes: str

SUPPORTED_SOURCES = [
    SourceHint("Google Patents", "Exported CSV or public patent page URL", "Use public pages only for lightweight demos; prefer exports/APIs for production."),
    SourceHint("EPO OPS", "XML/JSON transformed into PatentRecord fields", "Production use should implement OAuth credentials and EPO fair-use constraints."),
    SourceHint("USPTO / PatentsView", "CSV or JSON API results", "Recommended for reproducible bulk analytics workflows."),
]

def extract_patent_id_from_url(url: str) -> str:
    match = re.search(r"/patent/([^/?#]+)", url)
    return match.group(1) if match else "URL-" + stable_hash(url)

def fetch_google_patents_page(url: str, timeout: int = 20) -> PatentRecord:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "PatentLLM/0.1"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = clean_text(soup.find("title").get_text(" ")) if soup.find("title") else ""
    abstract_tag = soup.find(attrs={"class": re.compile("abstract", re.I)})
    abstract = clean_text(abstract_tag.get_text(" ")) if abstract_tag else ""
    claims = []
    for tag in soup.find_all(["claim-text", "div", "section"]):
        text = clean_text(tag.get_text(" "))
        if text.lower().startswith(("1.", "1 ")) and len(text) > 80:
            claims.append(text)
    return PatentRecord(
        patent_id=extract_patent_id_from_url(url), title=title.replace(" - Google Patents", ""),
        abstract=abstract, claims="\n".join(claims[:20]), source_url=url,
        metadata={"source": "google_patents_public_page"},
    )

def source_catalog() -> list[dict[str, Any]]:
    return [s.__dict__ for s in SUPPORTED_SOURCES]
