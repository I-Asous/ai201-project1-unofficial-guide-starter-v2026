#!/usr/bin/env python3
"""
Aggregate a run log in results/ into one row per criterion.

    python score_log.py results/run_2026-..._before.md

Reads the "Real output" section run_eval.py wrote (question, run, sources,
answer) and applies the checks in scorer.py. No model calls.
"""

import re
import sys
from pathlib import Path

import config
import scorer
import questions as qs
from chunker import split_documents
from ingest import load_documents

ENTRY = re.compile(
    r"### (?P<q>.+?) — run (?P<run>\d+)\n\n"
    r"- Best distance: (?P<dist>[\d.]+) \((?P<gate>passed|refused by) the gate\)\n"
    r"- Sources retrieved: (?P<src>.*?)\n\n```\n(?P<ans>.*?)\n```",
    re.S,
)
GATE_LINE = re.compile(r"Refused (\d+) of (\d+)")


def main(path: str) -> None:
    text = Path(path).read_text(encoding="utf-8")
    docs = load_documents()
    chunks = split_documents(docs)
    by_source: dict[str, list[str]] = {}
    for c in chunks:
        by_source.setdefault(c.source, []).append(c.text)
    source_text = {s: "\n".join(v) for s, v in by_source.items()}
    expects = {q["question"]: q["expects"] for q in qs.answered()}

    runs: dict[int, list[dict]] = {}
    for m in ENTRY.finditer(text):
        runs.setdefault(int(m["run"]), []).append(m.groupdict())

    from chunker import _split_title
    titles = {d.source: _split_title(d.text)[0] for d in docs}
    bad_chunks = scorer.chunks_ok(chunks, titles)

    gate = GATE_LINE.search(text)
    refused, total = (int(gate[1]), int(gate[2])) if gate else (0, 0)

    print(f"{path}\n")
    print("| Criterion | Target | " + " | ".join(f"Run {r}" for r in sorted(runs)) + " |")
    rows = {1: [], 2: [], 5: []}
    detail = []
    for r in sorted(runs):
        c1 = c2 = c5 = 0
        for e in runs[r]:
            ex = expects[e["q"]]
            srcs = [s.strip() for s in e["src"].split(",") if s.strip()]
            ok1 = scorer.retrieved_has_answer(ex, [source_text[s] for s in srcs if s in source_text])
            ok2 = scorer.names_a_source(e["ans"])
            ok5 = scorer.cited_source_correct(e["ans"], ex, source_text)
            c1 += ok1; c2 += ok2; c5 += ok5
            detail.append((r, e["q"], ok1, ok2, ok5, e["ans"].replace("\n", " ")[:110]))
        n = len(runs[r])
        rows[1].append(f"{c1} of {n}"); rows[2].append(f"{c2} of {n}"); rows[5].append(f"{c5} of {n}")
    k = len(runs)
    print(f"| 1. Retrieved chunk contains the answer | 4 of 5 | {' | '.join(rows[1])} |")
    print(f"| 2. Every answer names a source | 5 of 5 | {' | '.join(rows[2])} |")
    print(f"| 3. Gate stops out-of-corpus questions | 4 of 5 | {' | '.join([f'{refused} of {total}']*k)} |")
    print(f"| 4. Zero chunks missing title / ending mid-sentence | 0 violations | {' | '.join([f'{len(bad_chunks)} violations']*k)} |")
    print(f"| 5. Cited source contains the answer | 4 of 5 | {' | '.join(rows[5])} |")
    print("\nPer question (run, c1, c2, c5, answer start):")
    for r, q, a, b, c, ans in detail:
        print(f"  run {r}  c1={'Y' if a else 'N'} c2={'Y' if b else 'N'} c5={'Y' if c else 'N'}  {q[:48]:48} | {ans}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
