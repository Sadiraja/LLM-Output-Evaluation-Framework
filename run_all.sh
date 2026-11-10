#!/usr/bin/env bash
# Reproduces results/ using the offline simulator. For real models see README.
set -e
python scripts/build_testset.py
python -m unittest discover -s tests
python -m llm_eval run --variants v1@mock-large v2@mock-large
python -m llm_eval agreement      # uses data/manual_labels.jsonl
python -m llm_eval report
