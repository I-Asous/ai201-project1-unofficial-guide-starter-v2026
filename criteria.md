# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Most of my corpus is one post per topic, so a good retriever should land on the
right post for a plain question. The risk is the near-duplicates: seven
buildings have laundry posts that differ only in their prices, and every course
has three posts (overview, exams, workload). Two of my five questions (Aldridge
laundry, CS 340 hours) are aimed at exactly that, so I expect them to be the
ones that miss. 4 of 5 lets me miss one of those; 5 of 5 would be a target I
have no evidence I can hit, and 3 of 5 would forgive missing both.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
The prompt in generate.py labels every chunk `[from filename]`, and the gate
refuses before the model runs when nothing is close, so a refusal is the only
answer that legitimately has no source. That makes all five achievable, not four
of five: the only way to miss is the model ignoring the labels, and that is a
prompt failure I would want to see rather than budget for.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
Written before I measured anything. The out-of-scope questions (Mongolia, diesel
engines, the World Cup, ibuprofen, Rust) share no vocabulary with a corpus about
dining halls and dorms, so I expect them to be far from every chunk. The one I
am least sure of is ibuprofen, because the corpus has a health centre post. 4 of
5 leaves room for that one. I will fill in the measured gap after Milestone 4.

> **Measured in Milestone 4 (note, not a revision):** best distances were
> 0.82 to 0.93 for the five out-of-scope questions against 0.19 to 0.36 for my
> five test questions, a clean gap of about 0.47, so 0.6 sits in it and I expect
> 5 of 5, ibuprofen included (0.84, nearest chunk was a textbook post, not the
> health centre). The catch: campus-adjacent questions the corpus doesn't cover
> ("How much is tuition per semester?" 0.527, "Is there a gym on campus?" 0.570)
> score as close as loosely worded questions it does cover (0.40 to 0.52), so
> those pass the gate and rely on the prompt to decline. This criterion doesn't
> test them, which is a limit of the criterion.

---

## 4. Something about your chunks

<!-- YOU WRITE THIS ONE.

     How would you know if your chunks were the right size? Name something
     countable or observable.

     Examples of the right shape — don't copy these, they should come from
     what you actually saw in Milestone 3:
       - "At least 4 of 5 sampled chunks read as a complete thought, with no
          sentence cut in half at either end."
       - "No chunk is shorter than 200 characters, since anything below that
          in my corpus turned out to be a heading with no content under it." -->

Every chunk begins with its document's title line, and no chunk ends in the
middle of a sentence. Checked across all chunks, not a sample: zero violations.



**Why this target:**
Reading the documents, the first line of each is a title ("Laundry in Fenwick
Court") and the body often never repeats it: the Fenwick, Calder, Aldridge,
Innisfree, Morrow, Brewhouse and Tamsin laundry posts share the sentence "eight
washers and six dryers for the building". If a chunk lost its title, it could
not be told apart from six others. And every document is under 700 characters,
so there is no reason to cut a sentence anywhere. Zero, not "most", because
both failures are mechanical and a chunker can simply not do them.

---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. It could be about
     speed, about refusals, about a particular kind of question your corpus
     handles badly, about source attribution being correct rather than merely
     present — anything, as long as it names a number or an observable
     outcome. -->

Source attribution is correct, not just present: for at least 4 of my 5 test
questions, the source file the answer cites is one that actually contains my
`expects` phrase.

**Why this target:**
Criterion 2 only checks that a source is named. With seven near-identical
laundry posts and three posts per course, a wrong source is easy to name, and a
student who follows a wrong citation is worse off than one who gets none. 4 of 5
mirrors criterion 1 because a citation cannot be right if retrieval missed.


---

## Added in unit 2 (additions, not revisions — criteria 1 to 5 above are unchanged)

The first run met all five criteria, in all three runs. That says my five
targets were easy for this corpus, not that the system is done: criterion 3 only
uses clearly foreign questions (Mongolia, Rust), which any relevance gate
handles. The realistic failure is a question about campus life that the
documents happen not to cover, and the reverse, a casual question they do
cover that the gate refuses. Two more criteria, measured end to end with
`run_stress.py` on the two sets at the bottom of `questions.py`, three runs each.

### 6. Uncovered campus questions are declined

For at least 9 of the 10 questions in `ADJACENT_UNCOVERED` ("How much is tuition
per semester?", "Is there a gym on campus?"), the system declines, either
because the gate refuses or because the model says the documents don't cover it.

**Why this target:** The gate is one distance cutoff and I measured these
questions at 0.46 to 0.79, straddling 0.6, so the gate alone can't do it and I
expect the prompt to carry some. 9 of 10, not 10, because "Are pets allowed in
the dorms?" is close enough to real housing posts that I'd forgive one slip.

### 7. Casual questions the documents cover are answered

For 10 of the 10 questions in `LOOSE_COVERED` ("is the shuttle free", "cheap way
to get books"), the system gives an answer containing the fact in `expects`.

**Why this target:** A guide that says "I don't have enough information" about
something it does know is failing silently, and nobody can tell from the
refusal that the answer existed. I already measured one of these ("is the
shuttle free") at 0.648, over the 0.6 cutoff, so I expect a miss here. I'm
setting 10 of 10 rather than 9 because every false refusal is a real student
who leaves without the answer.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
