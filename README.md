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

## Run Log — Before

Five criteria from `criteria.md`, three runs each, produced by
`run_eval.py --label before` (`results/run_2026-09-20_2151_before.md`) and
aggregated per criterion by `score_log.py` using the checks in `scorer.py`.
Criteria 6 and 7 are additions I wrote in unit 2 after this first run met all
five; they come from `run_stress.py --label before`
(`results/stress_2026-09-20_2158_before.md`). Criterion 3 is one deterministic
pass, so the same number is in all three columns. Criterion 4 is also
deterministic (it checks the chunks, not the answers).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. No chunk missing its title or ending mid-sentence | 0 violations | 0 | 0 | 0 | MET |
| 5. Cited source file contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 6. Uncovered campus questions declined (added) | 9 of 10 | 10 of 10 | 10 of 10 | 10 of 10 | MET |
| 7. Covered casual questions answered (added) | 10 of 10 | 8 of 10 | 8 of 10 | 8 of 10 | **MISSED** |

Real output for each criterion, from run 1 unless it says otherwise.

**Criterion 1** — `store.py::search`, chunks from `chunker.py::split_documents`.
For "How much does a dryer cost in Aldridge Hall?" the five chunks retrieved
were `housing_aldridge_hall.txt`, `housing_aldridge_hall_laundry.txt`,
`housing_calder_annexe.txt`, `housing_calder_annexe_laundry.txt` and
`housing_innisfree_hall_laundry.txt`. The second one contains "$1.50 dry".

**Criterion 2 and 5** — `generate.py::answer_from_chunks`:

```
A dryer in Aldridge Hall costs $1.50. 

Source: housing_aldridge_hall_laundry.txt (also mentioned in housing_aldridge_hall.txt)
```

```
CS 340 Databases takes 15 hours a week in the last three weeks when the project lands (source: `course_cs_340_workload.txt` and `course_cs_340.txt`).
```

**Criterion 3** — `run_eval.py::check_out_of_scope` with `gate.py::check`, cutoff 0.6:

```
  refused  (best distance 0.825)  What is the capital of Mongolia?
  refused  (best distance 0.934)  How do I change the oil in a diesel engine?
  refused  (best distance 0.886)  Who won the 1994 World Cup?
  refused  (best distance 0.844)  What is the recommended dosage of ibuprofen for a headache?
  refused  (best distance 0.896)  How do I write a for loop in Rust?
  -> gate refused 5 of 5
```

**Criterion 4** — `python chunker.py`, `chunker.py::split_documents`:

```
88 chunks, 317 characters on average (shortest 178, longest 549), produced by chunker.py::split_documents
criterion 4: 0 chunks missing their title, 0 ending mid-sentence
```

**Criterion 6** — `run_stress.py` through `gate.py::check` and `generate.py::answer_from_chunks`.
Four of the ten passed the gate (0.46 to 0.57) and the model declined them
itself; the other six were refused by the gate (0.62 to 0.79):

```
Q: Is there a gym on campus?          (best distance 0.570, handled by model)
I don't have enough information to answer whether there is a gym on campus.

Q: What time does the bookstore close on Sundays?   (0.504, handled by model)
I don't have enough information to answer your question, as the provided documents do not mention the bookstore or its operating hours.
```

**Criterion 7** — the two misses, `run_stress.py`, same output in all three runs:

```
Q: is the shuttle free          (best distance 0.648, handled by gate.py::check)
I don't have enough information about that.

Q: can i study at the library late          (best distance 0.550, handled by model)
I do not have enough information to answer whether you can study at the library late, as the provided documents do not mention library hours.
```

## Verdicts

Against the targets I wrote in unit 1 (criteria 1 to 5) and the ones I wrote
before the stress run (6 and 7). No target was changed.

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Answer in retrieved chunks, 4 of 5 | MET | 5 of 5 in all three runs. Not close. |
| 2 | Every answer names a source, 5 of 5 | MET | 5 of 5 in all three runs; each answer contains a `.txt` filename. |
| 3 | Gate refuses out-of-corpus, 4 of 5 | MET | 5 of 5; nearest was ibuprofen at 0.844, 0.24 past the cutoff. |
| 4 | Zero chunks missing a title or ending mid-sentence | MET | Checked all 88 chunks, not a sample: 0 violations. |
| 5 | Cited source contains the answer, 4 of 5 | MET | 5 of 5 in all three runs, including the Aldridge laundry question I expected to fail. |
| 6 | Uncovered campus questions declined, 9 of 10 | MET | 10 of 10 in all three runs. I read the answers for the four the model handled; all four say the documents don't cover it. |
| 7 | Covered casual questions answered, 10 of 10 | **MISSED** | 8 of 10 in all three runs, the same two every time: "is the shuttle free" and "can i study at the library late". The target has to hold and it didn't. |

## Diagnoses

Criteria 1 to 5 met their targets with room to spare, so the honest reading is
that **my targets were set low.** Criterion 3 is the clearest case: its five
questions (Mongolia, Rust) share no vocabulary with a corpus about dorms, so
any cutoff passes them. Criterion 1 at 4 of 5 was never at risk, because every
one of my questions was well-formed. If I tightened one it would be criterion 3,
to campus-adjacent questions instead of foreign ones. That is why I added 6 and
7, and they are where the misses are.

Criterion 7 missed on two questions, and the mechanisms differ:

1. **"is the shuttle free" — gate stage.** The right document,
   `transit_shuttle.txt`, ranks **#1**, at a distance of 0.648. The cutoff was
   0.6, so `gate.py::check` refused before the model ever ran. Retrieval did its
   job and the gate threw the result away. A four-word lowercase query is far
   from a paragraph about several things (loop times, timetable, the free fare,
   which stop gets skipped) in embedding space, so a correct match still scores
   about 0.65, where my formal unit 1 questions scored 0.19 to 0.36.
2. **"can i study at the library late" — retrieval stage.** The right document,
   `study_library_hours.txt` ("Open until 2am during term..."), ranks **#9** at
   0.641. The top five were `admin_library_holds`, `money_jobs`,
   `study_group_rooms`, `money_textbooks` and `admin_pass_fail_option`, so it
   never reached the model, which honestly said the documents don't mention
   library hours. The query says "study" and "late", the document says "hours"
   and "2am" and never uses either word, so embedding similarity ranks posts
   about libraries and studying above it. A slightly different wording
   ("what time does the library close") puts it at #1, distance 0.443.

The pattern is the same underneath: casual, short queries sit about 0.3 further
from the right document than the formal ones I wrote in unit 1. The two misses
just show up at different stages.

## The Improvement

**What I changed:** `config.THRESHOLD` from 0.6 to 0.7. Nothing else.

**Why I picked it:** It fixes diagnosis 1 directly: the right document was
first, and the gate discarded it at 0.648. The highest distance for any question
the corpus covers is 0.648, and the lowest for a clearly foreign one is 0.825,
so 0.7 stays inside that gap.

I did not also fix diagnosis 2, on purpose: two changes at once would leave me
unable to say which one moved the numbers. Raising the cutoff has a cost I
expected: campus-adjacent uncovered questions between 0.6 and 0.7 now reach the
model instead of being refused by the gate. Criterion 6 is the check on that.

### Run Log — After

`run_eval.py --label after` (`results/run_2026-09-20_2200_after.md`) and
`run_stress.py --label after` (`results/stress_2026-09-20_2205_after.md`), three
runs each.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 2. Every answer names a source | 5 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 4. No chunk missing its title or ending mid-sentence | 0 violations | 0 | 0 | 0 | MET |
| 5. Cited source file contains the answer | 4 of 5 | 5 of 5 | 5 of 5 | 5 of 5 | MET |
| 6. Uncovered campus questions declined | 9 of 10 | 10 of 10 | 10 of 10 | 10 of 10 | MET |
| 7. Covered casual questions answered | 10 of 10 | 9 of 10 | 9 of 10 | 9 of 10 | **MISSED** |

**Did it help?** Yes, on the thing I aimed at. Criterion 7 went from 8 of 10 to
9 of 10 in all three runs, and the question that changed is the shuttle one:

```
Q: is the shuttle free          (best distance 0.648, now passes the gate)
Yes, the campus shuttle is free with a student ID (transit_shuttle.txt).
```

I know it was the cutoff and nothing else because it is the only file that
changed between the two runs, and the distance for that question is identical
(0.648); the only difference is which side of the cutoff it falls on.

The cost I expected did not show up in the measurement. The three uncovered
questions that the gate used to catch at 0.62 to 0.63 (scholarship, swimming
pool, pets) now reach the model, and it declined all three in every run
("...none of the provided documents mention pets"), so criterion 6 stayed at 10
of 10. Criteria 1 to 5 did not move. What I cannot claim is that this holds
beyond these ten questions: the prompt in `generate.py` is now doing work the
gate used to do, and ten questions is a small sample.

## What's Still Broken

**Criterion 7, one question: "can i study at the library late".** Diagnosis 2 is
untouched by the cutoff, because the gate isn't what stops it: the right
document is at rank 9, outside `TOP_K = 5`. What I would try, in order:

- `TOP_K = 10`. I checked this offline without spending a model call: the
  document is at rank 9, so it would be inside the top 10. It is the cheapest
  fix, but it also hands the model twice as much text, and I haven't measured
  whether that makes answers to the other questions worse or more expensive.
- Hybrid search with `rank-bm25` (already installed). That wouldn't obviously
  help here, because the query words "study" and "late" don't appear in the
  document, so I would not expect a keyword score to rank it first. I'd want to
  measure that before believing it.

I stopped here because the unit asks for one fix with its effect measured, and
a second change made in the same pass would have muddied that. I did not spend
the time to run either option.

Two smaller caveats:

- **My stress sets are small and I looked at them before choosing the fix.**
  I had already seen the distances for five of the ten uncovered questions and
  the shuttle question when I picked 0.7, so the improvement is partly tuned to
  them. Ten questions per set is enough to show the mechanism, not to promise
  0.7 is right for questions I haven't seen.
- **Criterion 6 depends on phrase matching.** `run_stress.py` decides "the
  model declined" from a list of phrases. I read the answers for every question
  the model handled and they were all real declines, but a differently worded
  decline would be counted as an answer.

## What I'd Do Differently

- **Criterion 3.** I would write it against campus-adjacent questions, not
  foreign ones. As written it tests the one case the gate cannot get wrong, so
  meeting it told me nothing. The ibuprofen worry I wrote down in unit 1 turned
  out to be wrong (it scored 0.844); the real risk was somewhere I hadn't looked.
- **Criterion 1.** It should be about casual queries, or it should say "top 3",
  not "top 5". All five of my test questions were phrased the way a careful
  person writes, and the two failures came from questions phrased the way a
  student actually types.
- **Criterion 5.** I would make it stricter: the cited source must be the
  document the fact came from, not any document that contains the phrase. Aldridge
  laundry is mentioned in two posts, and my check accepted either.
- **My test questions in general.** I wrote them after reading the documents, so
  they echo the documents' wording. The next set should be written by someone
  who hasn't read the corpus.

I also changed `REQUESTS_PER_MINUTE` in `config.py` from 30 to 12 during this
unit, because my free-tier key returned 429 at 30 (its limit is 15 per minute).
That is a fix to the environment, not part of the improvement above.
