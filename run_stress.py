#!/usr/bin/env python3
"""
Unit 2 stress test: criteria 6 and 7 in criteria.md, measured end to end.

    python run_stress.py --label before
    python run_stress.py --label after

Runs the ADJACENT_UNCOVERED and LOOSE_COVERED sets from questions.py through
retrieval, the gate and (when the gate passes) the model, three runs each, with
caching off. A question the gate refuses costs no model call.

Criterion 6: uncovered question is DECLINED, by the gate or by the model saying
the documents don't cover it. Criterion 7: covered question is ANSWERED with the
fact in `expects`. The phrase list below decides "the model declined"; every
answer is written to the log so the classification can be checked by reading.
"""

import argparse
import datetime as dt

import config
import gate
import questions as qs
import scorer
from generate import answer_from_chunks, usage
from store import search

DECLINE_PHRASES = (
    "don't have enough information", "do not have enough information",
    "not mentioned", "doesn't mention", "does not mention", "not covered",
    "no information", "don't have information", "do not have information",
    "not contain", "isn't mentioned", "cannot find", "can't find",
)


def declined(answer: str) -> bool:
    a = answer.lower()
    return any(p in a for p in DECLINE_PHRASES)


def ask(question: str, corpus, variant):
    results = search(question, top_k=config.TOP_K, corpus=corpus, variant=variant)
    decision = gate.check(results)
    if not decision.passed:
        return gate.REFUSAL, decision, "gate"
    return answer_from_chunks(question, results, cache=False), decision, "model"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--label", default="")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--corpus", default=None)
    p.add_argument("--variant", default="default")
    args = p.parse_args()

    log, c6, c7 = [], [0] * args.runs, [0] * args.runs
    for run in range(args.runs):
        for q in qs.ADJACENT_UNCOVERED:
            ans, d, who = ask(q, args.corpus, args.variant)
            ok = who == "gate" or declined(ans)
            c6[run] += ok
            log.append(("6", run + 1, q, "declined" if ok else "ANSWERED", d, who, ans))
        for item in qs.LOOSE_COVERED:
            q = item["question"]
            ans, d, who = ask(q, args.corpus, args.variant)
            ok = who == "model" and any(scorer.contains(ans, e) for e in item["expects"].split("|"))
            c7[run] += ok
            log.append(("7", run + 1, q, "answered" if ok else "MISSED", d, who, ans))
        print(f"run {run+1}: criterion 6 = {c6[run]} of {len(qs.ADJACENT_UNCOVERED)}, "
              f"criterion 7 = {c7[run]} of {len(qs.LOOSE_COVERED)}")

    config.RESULTS_DIR.mkdir(exist_ok=True)
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"stress_{dt.datetime.now():%Y-%m-%d_%H%M}{label}.md"
    lines = [
        f"# Stress run{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_stress.py::main`; retrieval `store.py::search`; "
        "gate `gate.py::check`; answers `generate.py::answer_from_chunks`",
        f"- Corpus: `{args.corpus or config.CORPUS}` · top-k {config.TOP_K} · relevance cutoff {config.THRESHOLD} · caching off",
        f"- When: {dt.datetime.now():%Y-%m-%d %H:%M}",
        "",
        "| Criterion | Target | " + " | ".join(f"Run {i+1}" for i in range(args.runs)) + " |",
        "|---|---|" + "---|" * args.runs,
        f"| 6. Uncovered campus questions declined | 9 of 10 | " + " | ".join(f"{n} of {len(qs.ADJACENT_UNCOVERED)}" for n in c6) + " |",
        f"| 7. Covered casual questions answered | 10 of 10 | " + " | ".join(f"{n} of {len(qs.LOOSE_COVERED)}" for n in c7) + " |",
        "", "## Every answer", "",
        "| Crit | Run | Question | Best distance | Handled by | Result |", "|---|---|---|---|---|---|",
    ]
    for crit, run, q, res, d, who, _ in log:
        lines.append(f"| {crit} | {run} | {q} | {d.best_distance:.3f} | {who} | {res} |")
    lines += ["", "## Real output", ""]
    for crit, run, q, res, d, who, ans in log:
        lines += [f"### [{crit}] {q} — run {run}", "", f"- Best distance {d.best_distance:.4f}, handled by {who}, result: {res}", "", "```", ans, "```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print(usage())


if __name__ == "__main__":
    main()
