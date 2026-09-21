"""
Your test questions.

Milestone 2 asks you to write five questions your system should be able to
answer from your corpus, specific enough to have a right answer.

  ✗ "What are good dining halls?"          — no right answer
  ✓ "What do students say about wait times at Commons during lunch?"

Fill in `QUESTIONS` below. `expects` is a word or short phrase you'd expect a
correct answer to contain — you'll use it in unit 2 when you build a scorer,
and having written it now means you decided what "correct" meant before you saw
any results.

`OUT_OF_SCOPE` holds five questions your documents clearly don't cover. You
need these in Milestone 4 to find where your relevance cutoff belongs, and
again in unit 2, where `run_eval.py` runs them through the gate and writes what
happened into your run log — that's the evidence for criterion 3.

Swap them for your own if you like. Keep five of them either way: criterion 3
names a target of "4 of 5", and four of three is not a thing.
"""

QUESTIONS = [
    # Housing lottery: the answer contradicts the obvious assumption ("random").
    {"question": "Is the housing lottery random for seniors?",
     "expects": "credit hours"},
    # Near-duplicate trap: seven buildings have laundry posts that read almost
    # identically. Only the price tells them apart.
    {"question": "How much does a dryer cost in Aldridge Hall?",
     "expects": "$1.50"},
    {"question": "How long is the wait at Kestrel Commons around 12:30?",
     "expects": "20 to 25 minutes"},
    # The detail the document itself calls "the part nobody mentions".
    {"question": "How late in the semester can I choose pass/fail for a course?",
     "expects": "week eight"},
    # Three posts exist for every course (overview, exams, workload).
    {"question": "How many hours a week does CS 340 Databases take near the end of the term?",
     "expects": "15"},
]

# Questions from a different world entirely. Your gate should refuse all five.
#
# There are five of these because criterion 3 in criteria.md names a target of
# "at least 4 of 5" — you need five things to try before you can report 4 of 5.
# `run_eval.py` runs these through retrieval and the gate on every eval and
# records what happened, so criterion 3 has evidence in the run log alongside
# the others. They cost no model calls: a refusal never reaches the model.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions you've actually filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]


# ─── Unit 2 stress sets ──────────────────────────────────────────────────────
# Added in unit 2 after the first run met every criterion: the five criteria
# above turned out to be easy for this corpus. The out-of-scope questions are
# all clearly foreign, which is the case a relevance gate handles trivially.
# These two sets test the case that matters and that the gate finds hard.

# Campus questions the documents do NOT answer. The system should refuse.
ADJACENT_UNCOVERED = [
    "How much is tuition per semester?",
    "Is there a gym on campus?",
    "What time does the bookstore close on Sundays?",
    "Which dorm has the best view?",
    "How do I join the rowing team?",
    "How do I apply for a scholarship?",
    "Is there a swimming pool on campus?",
    "Who is the president of the university?",
    "How do I get a bike repaired on campus?",
    "Are pets allowed in the dorms?",
]

# Loosely worded questions the documents DO answer. The system should answer.
# `expects` may list alternatives separated by "|"; any one counts.
LOOSE_COVERED = [
    {"question": "where can i get food late at night", "expects": "Verrill"},
    {"question": "anything i should know before winter", "expects": "layers"},
    {"question": "cheap way to get books", "expects": "reserve|price-match"},
    {"question": "how bad is the workload for bio", "expects": "9 to 11"},
    {"question": "which dorm is closest to the science labs", "expects": "Aldridge"},
    {"question": "is the shuttle free", "expects": "student ID"},
    {"question": "can i study at the library late", "expects": "2am"},
    {"question": "what happens to leftover printing money", "expects": "not roll over|does not roll"},
    {"question": "how do i get my transcript for free", "expects": "unofficial"},
    {"question": "is there anywhere on campus with real coffee", "expects": "espresso|Ridgeway"},
]
