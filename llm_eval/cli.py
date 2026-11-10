import argparse
import json
from pathlib import Path

from .agreement import compute_agreement, make_sample_sheet
from .backends import AnthropicClient
from .judge import HeuristicJudge, LLMJudge
from .report import build_report
from .runner import run


def main(argv=None):
    p = argparse.ArgumentParser(prog="llm_eval", description="Automatic LLM output evaluation")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="evaluate variants over a test set and write a report")
    r.add_argument("--testset", default="data/test_set.jsonl")
    r.add_argument("--variants", nargs=2, required=True, metavar=("A", "B"),
                   help="two variants as <prompt_version>@<model>, e.g. v1@claude-haiku-5-5 v2@claude-haiku-5-5")
    r.add_argument("--judge", choices=["heuristic", "anthropic"], default="heuristic")
    r.add_argument("--judge-model", default="claude-sonnet-5-5")
    r.add_argument("--out", default="results")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--limit", type=int)

    s = sub.add_parser("sample", help="write a blind sheet of 20 samples to label by hand")
    s.add_argument("--results", default="results/results.jsonl")
    s.add_argument("--out", default="results/manual_label_sheet.jsonl")
    s.add_argument("-n", type=int, default=20)

    a = sub.add_parser("agreement", help="compare judge scores with manual labels")
    a.add_argument("--results", default="results/results.jsonl")
    a.add_argument("--labels", default="data/manual_labels.jsonl")
    a.add_argument("--out", default="results/agreement.json")

    q = sub.add_parser("report", help="(re)build report.md from results")
    q.add_argument("--out", default="results")

    args = p.parse_args(argv)
    if args.cmd == "run":
        judge = HeuristicJudge() if args.judge == "heuristic" else LLMJudge(AnthropicClient(args.judge_model))
        rows, meta = run(args.testset, args.variants, judge, args.out, args.workers, args.limit)
        print(f"{len(rows)} rows -> {args.out}/results.jsonl")
        print(build_report(args.out, Path(args.out) / "agreement.json"))
    elif args.cmd == "sample":
        sheet = make_sample_sheet(args.results, args.out, args.n)
        print(f"wrote {len(sheet)} samples -> {args.out}")
    elif args.cmd == "agreement":
        ag = compute_agreement(args.results, args.labels)
        Path(args.out).write_text(json.dumps(ag, indent=2))
        print(json.dumps({k: v for k, v in ag.items() if k != "disagreements"}, indent=2))
    elif args.cmd == "report":
        print(build_report(args.out, Path(args.out) / "agreement.json"))


if __name__ == "__main__":
    main()
