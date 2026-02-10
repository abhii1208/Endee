"""
Evaluate retrieval quality by calling /search and computing recall@k and MRR.
Requires the app to be running (e.g. uvicorn) and sample data ingested.
Usage: python -m scripts.evaluate_retrieval [--base-url http://localhost:8000]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parents[1]
QUERIES_PATH = BASE_DIR / "data" / "evaluation_queries.json"


def load_queries(path: Path) -> list:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def recall_at_k(returned_ids: list, expected_ids: list, k: int) -> float:
    if not expected_ids:
        return 1.0
    top_k = returned_ids[:k]
    hits = sum(1 for eid in expected_ids if eid in top_k)
    return hits / len(expected_ids)


def mrr(returned_ids: list, expected_ids: list) -> float:
    if not expected_ids:
        return 1.0
    for rank, rid in enumerate(returned_ids, start=1):
        if rid in expected_ids:
            return 1.0 / rank
    return 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    if not QUERIES_PATH.exists():
        print(f"Missing {QUERIES_PATH}")
        sys.exit(1)

    queries = load_queries(QUERIES_PATH)
    recalls_ticket, recalls_faq, recalls_runbook = [], [], []
    mrrs_ticket, mrrs_faq, mrrs_runbook = [], [], []

    with httpx.Client(timeout=30.0) as client:
        for entry in queries:
            q = entry["query"]
            expected = entry["expected_ids"]
            resp = client.post(
                f"{args.base_url.rstrip('/')}/search",
                json={"query": q, "top_k": args.k, "generate_answer": False},
            )
            resp.raise_for_status()
            data = resp.json()

            def ids(typ: str) -> list:
                return [x["id"] for x in data.get(typ, [])]

            rt = recall_at_k(ids("tickets"), expected.get("tickets", []), args.k)
            rf = recall_at_k(ids("faqs"), expected.get("faqs", []), args.k)
            rr = recall_at_k(ids("runbooks"), expected.get("runbooks", []), args.k)
            recalls_ticket.append(rt)
            recalls_faq.append(rf)
            recalls_runbook.append(rr)

            mt = mrr(ids("tickets"), expected.get("tickets", []))
            mf = mrr(ids("faqs"), expected.get("faqs", []))
            mr = mrr(ids("runbooks"), expected.get("runbooks", []))
            mrrs_ticket.append(mt)
            mrrs_faq.append(mf)
            mrrs_runbook.append(mr)

    n = len(queries)
    print("Recall@{} (mean over {} queries):".format(args.k, n))
    print("  tickets:  {:.3f}".format(sum(recalls_ticket) / n))
    print("  faqs:     {:.3f}".format(sum(recalls_faq) / n))
    print("  runbooks: {:.3f}".format(sum(recalls_runbook) / n))
    print("MRR (mean):")
    print("  tickets:  {:.3f}".format(sum(mrrs_ticket) / n))
    print("  faqs:     {:.3f}".format(sum(mrrs_faq) / n))
    print("  runbooks: {:.3f}".format(sum(mrrs_runbook) / n))


if __name__ == "__main__":
    main()
