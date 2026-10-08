#!/usr/bin/env bash
set -euo pipefail
patentllm ingest data/sample/sample_patents.jsonl
patentllm report --query "battery thermal management systems for electric vehicles" --audience rd
