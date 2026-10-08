from __future__ import annotations
import hashlib, re
from pathlib import Path

def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text))
    text = text.replace(" ,", ",").replace(" .", ".")
    return text.strip()

def stable_hash(*parts: str, length: int = 12) -> str:
    raw = "::".join(parts).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:length]

def ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def split_list_field(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(str(v)) for v in value if clean_text(str(v))]
    text = clean_text(str(value))
    if not text:
        return []
    parts = re.split(r"[;|]", text)
    return [p.strip() for p in parts if p.strip()]
