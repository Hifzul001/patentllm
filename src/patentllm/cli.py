from __future__ import annotations
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from patentllm.evaluation.benchmark import benchmark_models
from patentllm.evaluation.evaluator import evaluate_file
from patentllm.pipeline import build_index, generate_report, ingest_files, run_demo
from patentllm.reporting.renderers import save_report_files
from patentllm.schemas import Audience, ReportRequest
from patentllm.storage import init_db, load_patents

app = typer.Typer(help="PatentLLM command-line interface.")
console = Console()

@app.command()
def init() -> None:
    init_db()
    console.print("[green]Database initialised.[/green]")

@app.command()
def ingest(paths: list[str]) -> None:
    count = ingest_files(paths)
    chunks = build_index()
    console.print(f"[green]Ingested {count} patents and indexed {chunks} chunks.[/green]")

@app.command("list-patents")
def list_patents_cmd() -> None:
    patents = load_patents()
    table = Table(title="PatentLLM Corpus")
    table.add_column("Patent ID")
    table.add_column("Title")
    table.add_column("Assignees")
    for p in patents:
        table.add_row(p.patent_id, p.title[:80], ", ".join(p.assignees))
    console.print(table)

@app.command()
def index() -> None:
    chunks = build_index()
    console.print(f"[green]Indexed {chunks} chunks.[/green]")

@app.command()
def report(
    query: str = typer.Option(..., help="Technology or competitor question."),
    audience: Audience = typer.Option(Audience.rd, help="rd, sales, marketing, or executive."),
    model: Optional[str] = typer.Option(None, help="Ollama model, e.g. llama3.1:8b."),
    top_k: int = typer.Option(5, help="Number of evidence chunks."),
    output_dir: str = typer.Option("reports", help="Directory for Markdown/JSON output."),
) -> None:
    result = generate_report(ReportRequest(query=query, audience=audience, model=model, top_k=top_k))
    md_path, json_path = save_report_files(result, output_dir=output_dir)
    console.print(f"[green]Report generated.[/green] Markdown: {md_path} JSON: {json_path}")

@app.command()
def demo() -> None:
    result = run_demo()
    md_path, json_path = save_report_files(result)
    console.print(f"[green]Demo complete.[/green] Markdown: {md_path} JSON: {json_path}")

@app.command()
def evaluate(
    labelled: str = typer.Option("data/sample/labelled_reports.jsonl"),
    model: Optional[str] = typer.Option(None),
    output: str = typer.Option("reports/eval_results.csv"),
) -> None:
    df = evaluate_file(labelled, model=model, output=output)
    console.print(df)
    console.print(f"[green]Saved evaluation results to {output}[/green]")

@app.command()
def benchmark(
    models: list[str] = typer.Option(..., help="One or more Ollama model names."),
    query: str = typer.Option(...),
    audience: Audience = typer.Option(Audience.rd),
    output: str = typer.Option("reports/model_benchmark.csv"),
) -> None:
    df = benchmark_models(models=models, query=query, audience=audience)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    console.print(df)
    console.print(f"[green]Saved benchmark to {output}[/green]")

if __name__ == "__main__":
    app()
