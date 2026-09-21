# The Unofficial Guide

Islam Asous — corpus: `campus_life`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

A question-answering system over `campus_life`, a corpus of 88 short posts
written the way one student answers another: dining halls, dorms, courses, and
the administrative rules nobody explains properly. It retrieves the closest
posts, refuses outright if nothing is close enough, and otherwise has Gemini
answer from those posts and name the file each fact came from. It answers
specific questions ("How much does a dryer cost in Aldridge Hall?", "How late
can I choose pass/fail?") and says "I don't have enough information about that"
for anything the posts don't cover.

## Chunking Strategy

**Chunk size:** 700 characters maximum (`config.CHUNK_SIZE`), but in practice one
whole post per chunk: all 88 documents are under 560 characters, so 88
documents become 88 chunks (avg 317, shortest 178, longest 549).
**Overlap:** 0

Reading the documents, three things decided this:

1. **Each post is one thought.** The useful fact sits in one or two sentences
   and the posts are 178 to 549 characters, so cutting one up only separates a
   fact from its context. I keep a post whole whenever it fits.
2. **The title line is the only place a building is named.** The seven laundry
   posts (Aldridge, Calder, Fenwick, Innisfree, Morrow, Brewhouse, Tamsin) all
   say "eight washers and six dryers for the building" and differ only in their
   prices. "Laundry in Fenwick Court" on the first line is the only thing that
   says which building. So if a document is ever split, every piece gets the
   title repeated at the top.
3. **There is nothing to overlap.** Splits fall on paragraph or sentence ends,
   so no half-thought straddles a boundary. Overlap is 0.

I started from the starter's 800/120 fixed windows. On this corpus they also
produce 88 chunks, one per post, so `split_documents` gives the same chunks on
today's data. I wrote it anyway because the fixed-window version would cut a
longer post mid-sentence and drop its title, and I wanted that property to be
true of the code and not just of this corpus. I tested it on a synthetic
1,800-character document: it split on sentence boundaries into three chunks of
697, 649 and 462 characters, each starting with the title. Chunk size dropped
from 800 to 700 to leave headroom under the limit; it changes nothing here.

## Sample Chunks

**Chunk 1** — source: `admin_add_drop_deadline.txt` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_biol_160.txt` — produced by: `chunker.py::split_documents`

```
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Expect 9 to 11 hours a week, the heaviest first-year course by reputation.

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

**Chunk 3** — source: `course_hist_118_workload.txt` — produced by: `chunker.py::split_documents`

```
Workload for HIST 118 Modern World History

People keep asking so: a lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `dining_pellew_dining_hall_followup.txt` — produced by: `chunker.py::split_documents`

```
Re: Pellew Dining Hall

Adding to what people have said about Pellew Dining Hall. The wait figure of 12 to 18 minutes at peak matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the furthest hall from anywhere, next to the athletics centre. Nobody tells you this at orientation.
```

**Chunk 5** — source: `housing_innisfree_hall.txt` — produced by: `chunker.py::split_documents`

```
Innisfree Hall — what it's actually like

Transferred in last year, so take this with a grain of salt. Built 1991, renovated 2022. Rooms are doubles arranged as pairs sharing one bathroom between two rooms.

The good: the shared-bathroom-between-two-rooms arrangement is the best compromise on campus.

The bad: no air conditioning, which matters for the first three weeks of September.

Laundry costs $1.75 wash, $1.75 dry, app-based. On noise: moderate; the building is L-shaped and the short wing is much quieter.
```

## Sample Answer

**Question:** Is the housing lottery random for seniors?

**Answer:**

```
  (best distance 0.194, cutoff 0.6)

No, the housing lottery is not entirely random for seniors; juniors and seniors are ordered by accumulated credit hours first, and only tie-break randomly (admin_housing_lottery.txt).

Sources retrieved: admin_housing_lottery.txt, advising_registration.txt, housing_morrow_house.txt, housing_old_brewhouse.txt, housing_tamsin_court.txt
```

**My relevance cutoff:** 0.6 (`config.THRESHOLD`, unchanged from the starter).

I ran my five test questions and the five `OUT_OF_SCOPE` questions and wrote
down the best (lowest) distance for each. The two groups don't touch: the
in-corpus questions top out at 0.356 and the out-of-scope ones start at 0.825.
That is a gap of about 0.47, and 0.6 sits inside it with 0.24 of margin above
the worst in-corpus question and 0.22 below the best out-of-scope one. I kept
the starter's number because the measurement supports it, not because it was
the default.

| Question | In corpus? | Best distance |
|---|---|---|
| Is the housing lottery random for seniors? | yes | 0.194 |
| How much does a dryer cost in Aldridge Hall? | yes | 0.356 |
| How long is the wait at Kestrel Commons around 12:30? | yes | 0.222 |
| How late in the semester can I choose pass/fail for a course? | yes | 0.226 |
| How many hours a week does CS 340 Databases take near the end of the term? | yes | 0.218 |
| What is the capital of Mongolia? | no | 0.825 |
| How do I change the oil in a diesel engine? | no | 0.934 |
| Who won the 1994 World Cup? | no | 0.886 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.844 |
| How do I write a for loop in Rust? | no | 0.896 |

**Where the cutoff stops working.** Those ten questions are the easy case: the
out-of-scope ones share no vocabulary with the corpus. I also tried five
loosely worded questions the corpus does cover ("where can i get food late at
night", 0.521; "my roommate is too loud what do i do", 0.511) and five
campus-adjacent questions it doesn't ("How much is tuition per semester?",
0.527; "Is there a gym on campus?", 0.570). Those two groups overlap, so no
cutoff separates them, and the tuition question passes the gate at 0.6. It was
still declined, by the prompt in `generate.py` ("tuition costs are not
mentioned in the provided documents"). So the gate catches the clearly foreign
questions and the prompt catches the near ones, which is how the starter
describes the two layers, and I saw it happen.

## How I Used AI

I used Claude Code (in VS Code) to do most of the Unit 1 work in this repo,
including the questions, criteria, chunker and this write-up. The two moments
below are the ones where its first output needed correcting.

**1.** I asked Claude to write the chunker after reading the corpus. Its first
draft packed a too-long paragraph into chunks by sentence but joined every
piece with a blank line, so sentences from one paragraph came out looking like
separate paragraphs. It tested the draft on a synthetic long document, saw the
problem, and changed the packer so each unit carries its own separator (blank
line between paragraphs, a space between sentences of the same paragraph). It
also checked criterion 4 across all 88 real chunks rather than a sample.

**2.** I asked Claude to set the relevance cutoff from measured distances. The
ten required questions gave a clean gap, and that alone would have justified
keeping 0.6. Claude went further and ran ten more questions I hadn't written:
five loosely worded and five campus-adjacent. That showed the gate cannot
separate near-domain questions the corpus doesn't cover from loosely worded ones
it does, which is why the README and `criteria.md` say where the gate stops
working instead of claiming it always works.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
