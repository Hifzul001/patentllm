from __future__ import annotations
import time
from dataclasses import dataclass
import httpx

@dataclass
class LLMResponse:
    text: str
    model: str
    latency_seconds: float
    used_fallback: bool = False

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, model: str, temperature: float = 0.1) -> LLMResponse:
        started = time.perf_counter()
        payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
        return LLMResponse(text=data.get("response", "").strip(), model=model, latency_seconds=time.perf_counter() - started)
