"""
Scoring for the five acceptance criteria in criteria.md.

`run_eval.py` finds `judge` here automatically and puts pass/fail in the Run
columns. `score_log.py` reads a run log and aggregates the same checks up to one
row per criterion, which is the shape the README asks for.

What each check means (targets are the ones written in criteria.md, unchanged):

  1. retrieved_has_answer  some retrieved chunk contains the `expects` phrase
  2. names_a_source        the answer names at least one .txt source file
  3. (gate)                measured by run_eval.py::check_out_of_scope, not here
  4. chunks_ok             every chunk starts with its title and ends a sentence
  5. cited_source_correct  a source file the answer names actually contains the
                           `expects` phrase — right source, not merely a source

`judge` is the per-question verdict: retrieval found the answer AND the answer
was cited to a source that has it. That is criterion 1 and criterion 5 together
on one run, so a question only passes if the answer is both findable and
correctly attributed. Criterion 2 is reported separately by score_log.py.
"""

import re

_SOURCE = re.compile(r"[A-Za-z0-9_\-]+\.(?:txt|md)")
_NUMBER_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
                 "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}


def normalize(text: str) -> str:
    """Lowercase, fold '20-25' / '20–25' to '20 to 25', spell numbers as digits."""
    text = text.lower()
    text = re.sub(r"(\d)\s*[-–—]\s*(\d)", r"\1 to \2", text)
    for word, digit in _NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", digit, text)
    return re.sub(r"\s+", " ", text)


def contains(text: str, expects: str) -> bool:
    return bool(expects.strip()) and normalize(expects) in normalize(text)


def cited_sources(answer: str) -> set[str]:
    return set(_SOURCE.findall(answer))


def retrieved_has_answer(expects: str, chunk_texts: list[str]) -> bool:
    return any(contains(t, expects) for t in chunk_texts)


def names_a_source(answer: str) -> bool:
    return bool(cited_sources(answer))


def cited_source_correct(answer: str, expects: str, source_texts: dict[str, str]) -> bool:
    return any(contains(source_texts.get(name, ""), expects) for name in cited_sources(answer))


def chunks_ok(chunks, titles: dict[str, str]) -> list[str]:
    """Labels of chunks that break criterion 4. Empty list means all good."""
    bad = []
    for c in chunks:
        title_ok = c.text.startswith(titles.get(c.source, ""))
        end_ok = c.text.rstrip().endswith((".", "!", "?", ")", '"'))
        if not (title_ok and end_ok):
            bad.append(c.label)
    return bad


def judge(question: str, expects: str, answer: str, results) -> bool:
    """Per-run verdict used by run_eval.py: findable AND correctly attributed."""
    texts = {r.source: r.text for r in results}
    found = retrieved_has_answer(expects, [r.text for r in results])
    return found and cited_source_correct(answer, expects, texts)
