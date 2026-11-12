# TakeMeter

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, the
> notebook, the baseline, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> head -5 data/practice_labels.csv     # the shape your labels.csv needs
> ```
>
> Then open `takemeter.ipynb` **in this folder** — in VS Code, or with
> `jupyter notebook` if you prefer. Pick the kernel: the `.venv` inside this
> project. Run section 1, which reports the hardware you'll be training on.
> Everything else waits until you have data.
>
> Nothing to upload, nothing to connect, no accounts and no keys. The notebook
> runs on your machine and writes next to your code.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     Unit 5 asks for the first five sections. Unit 6 adds the five below them.

     Everything is pasted as TEXT. No screenshots, no images.

     ⚠️ The confusion matrix especially. The notebook prints one as a markdown
     table, ready to copy. A screenshot of a matrix earns nothing. Paste the
     table.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 5 — THE BUILD ═══════════════════════ -->

## What This Does
TakeMeter sorts comments from Hacker News threads by **what the comment's claim
rests on**, not by what it says or how strongly it says it. Three labels:
`checkable` when a reader could go and verify the claim, `anecdote` when it
recounts an incident nobody else can check, and `assertion` when it offers
neither.

The question behind it is whether an argument is *supported* in a way a reader
can act on. A heated comment citing a public figure and a calm one asserting
the same thing from nowhere look similar and are worth very different amounts,
and HN threads are full of both.

---

## Label Taxonomy

<!-- Each label: a one-sentence definition and two real examples from your
     reading. Then your decision rule for the hardest boundary.

     The decision rule is worth a point on its own and it's the thing most
     people leave out. Every taxonomy has a hardest boundary. Name yours. -->

The community is Hacker News comment threads. The three labels sort a comment
by **what its claim rests on**, not by tone, and not by whether the claim is
correct.

### `anecdote`

**Definition:** Recounts a particular incident - whoever it happened to,
whoever is telling it - that a reader cannot independently verify.

**Example 1:**
> My daughter, when she pointed something out to me on my laptop screen, ALWAYS
> touched the screen from the time she could walk. When she was a teenager I
> asked her repeatedly to please stop touching the screen when she pointed
> something out, but I gave up.

**Example 2:**
> All I can tell you is of the last 10 I tried, all games from the last 10
> years, 8 run perfectly fine under Wine on Mac, and 2 of the older ones with a
> custom inhouse engine for only that game, run perfectly fine after telling an
> agent to make it work.

<!-- Example 2 is full of numbers and still `anecdote`: the run happened once,
     to one person, and nobody else can repeat it. -->

### `checkable`

**Definition:** Rests on something a reader could go and verify - a named fact,
figure, date, document, quote, event or rule - named specifically enough that a
reader would know what to check.

**Example 1:**
> Yes, the developer documentation used to publish the string until May 2026,
> when Anthropic removed it and removed the feature from the API. Sonnet's
> explanation was correct, just out of date

**Example 2:**
> It is illegal to download copyrighted material from a website and make copies
> of it in violation of its licence. I can't go scrape New York Times articles
> and make copies of them without first licensing them from NYT.

<!-- Example 2 supplies no link and still counts. That is the point of the
     label, and the reason it is not called `citation`. -->

### `assertion`

**Definition:** Rests on nothing a reader could check, and on no experience
either - an opinion, a prediction, an analogy, or an argument from reasoning
alone.

**Example 1:**
> Take a closer look at your own previous comment. Aside from stubbornly
> declaring "AI bad!", what you described there is market behavior. Markets can
> not be ignored.

**Example 2:**
> "racing cars" actually would not be stationary. "Race cars" are the class of
> vehicle, which can be stationary. If the cars are racing, they are not
> stationary.
>
> "High-speed" is ambiguous. It can be used to describe the class of vehicle,
> or it can be used to describe the state of motion of the vehicle.

### The hardest boundary

**Which two labels:** `checkable` vs `assertion`.

I found this one the hard way. My first taxonomy called the middle label
`citation` and required the writer to supply a source - a link, a quote, a named
document. Labelling 20 posts blind showed why that fails: a claim like
*"it is illegal to download copyrighted material"* names no source, but copyright
law is a real thing a reader can go and look up. It is not `anecdote`, because
no personal experience is involved. And it cannot be `assertion`, because that
label means *nothing to check*, and there plainly is something to check.

Three labels that did not cover the space. So the label is now `checkable`, and
the question is about the claim rather than about the writer's manners.

**The decision rule I used every time:**

> **Could another reader check this without taking the writer's word for it?**
> If yes, `checkable`. If not, does it recount a particular incident? Then
> `anecdote`. If it is neither - an opinion, a preference, a habit, a
> prediction, an argument - `assertion`.

Four consequences I applied consistently:

- **A link is not required.** A named law, a public event, a product's
  documented behaviour, a video everyone in the thread has seen: all
  `checkable`, supplied source or not.
- **But it must be named specifically enough to check.** *"Studies show"* and
  *"everyone knows"* name nothing, so they stay `assertion`. The test is whether
  a reader would know where to go.
- **An anecdote can be about anyone, told from any perspective.** It is not a
  first-person label. A story about a colleague, told in the third person, is
  as much an `anecdote` as one about the writer.
- **A preference is not an incident.** *"Laptops only for that kind of work,
  thanks"* and *"I always collapse the top comment"* report a taste and a habit,
  not something that happened, so both are `assertion`. This is the consequence
  that moved the most posts, and the one I got wrong first time round.

When a comment does both - a personal story plus a genuinely checkable fact - I
used rule 4 from the staff set as the tie-break and took whichever the comment
spends most of its words on.
---

## The Dataset
**Where the posts came from:** The Hacker News comment feed, through the public
Algolia API, collected with `collect_hn.py` in this repo. The API serves at most
1000 hits per query, so a single sweep tops out around 160 usable posts; the
collector gets past that by sweeping eight separate 24-hour windows, each with
its own budget. That keeps the sample broad rather than skewing it toward a
topic. 1263 posts went into `pool.csv`, and 240 of those were labelled.

Three collection filters, each of which shapes the data:

- **25–95 words.** A profile of 300 raw comments put the median at 30 words,
  with 23% under 15 and 12% over 95. The short ones carry no stance to learn,
  and anything past 95 words is truncated at `MAX_LENGTH = 128` anyway.
- **At most 3 comments per story.** 626 distinct stories are represented. Forty
  comments off one thread would teach the model that thread's vocabulary, and
  near-identical arguments landing in different splits is leakage.
- **Whitespace collapsed to single spaces.** Every word is kept; paragraph
  breaks are not.

**How I labelled them:** Three passes, and the `note` column in `labels.csv`
records which pass each post came from.

- **20 cold.** Drawn at random from the pool and labelled unaided, with no
  suggestion on screen. This is the control.
- **52 pre-labelled and checked.** Claude labelled them; I read each one and
  kept or overrode it.
- **168 pre-labelled, unchecked.** Claude's labels, applied under the final
  taxonomy but never individually reviewed by me. 70% of the corpus.

The disclosure matters because the corpus is not uniform. Two of those three
groups are mostly a model's judgement, and the agreement numbers below say how
far that judgement can be trusted.

**The taxonomy changed twice while labelling, and both changes were forced by
the data:**

1. The middle label started as `citation` and required the writer to *supply* a
   source. The cold 20 broke it: a claim like *"it is illegal to download
   copyrighted material"* names no source, is not an anecdote, and cannot be an
   `assertion` because that means *nothing to check*. Three labels that did not
   cover the space. Renamed `checkable`, with the test moved onto the claim.
2. `anecdote` was defined as *the writer's own experience*. That is not what the
   word means - an anecdote can be about anyone, told from any perspective - and
   the real test is whether it recounts a particular incident. Fixing that moved
   33 posts out of `anecdote`, which collapsed from about 50 to 17.

**Counts per label:**

| Label | Count | Share |
|---|---|---|
| `checkable` | 113 | 47.1% |
| `assertion` | 110 | 45.8% |
| `anecdote` | 17 | 7.1% |
| **Total** | **240** | 100% |

This misses my own criterion 3, which asked every label to sit between 25% and
45%. It passes the brief's 70% cap comfortably. The shape is a fact about
Hacker News under this taxonomy: comments there are overwhelmingly argument and
opinion, and recounted incidents are rare.

**Three hard cases**

**1.**
> *The post:* "It is illegal to download copyrighted material from a website and
> make copies of it in violation of its licence. I can't go scrape New York
> Times articles and make copies of them without first licensing them from NYT."
>
> *Could have been:* `checkable` or `assertion`.
>
> *I chose `checkable`, because:* copyright law is a real thing a reader can go
> and look up, even though the writer supplies no link. This is the post that
> broke the first version of the taxonomy and forced the `citation` →
> `checkable` rename.

**2.**
> *The post:* "I have the same M1/16GB on newest macos, that thing still flies.
> My work device is an M4/32GB. The difference doesnt feel that big, especially
> when you code mostly with agents."
>
> *Could have been:* `anecdote` or `assertion`.
>
> *I chose `assertion`, because:* nothing happened in it. It reports an ongoing
> impression of two machines, not an incident. This post was my own README
> example for `anecdote` until the definition was fixed, at which point it
> stopped qualifying as an example of its own label.

**3.**
> *The post:* "This [0] is my secret weapon against this kind of slop. Any time
> I see any of these markers I tell my agent to read this again. Works
> unreasonably well. [0] https://gist.githubusercontent.com/..."
>
> *Could have been:* `checkable` or `anecdote`.
>
> *I chose `checkable`, because:* the gist is linked and anyone can read it. The
> claim that it "works unreasonably well" is unverifiable, but the comment
> spends most of its words pointing at the artefact, and rule 4 of the staff
> taxonomy breaks that tie toward whichever the post spends most of its words on.

---

## The Training Run
**Base model:** `distilbert-base-uncased`.

**Settings:** 3 epochs, learning rate 2e-5, batch size 16, `MAX_LENGTH` 128,
seed 42.

**Anything I changed from the defaults, and why:** Nothing. The only change to
the notebook was `LABELS`, set to this project's three. Raising `EPOCHS` was
tempting once the accuracy came in at 0.500, but the problem is not
undertraining - it is 17 examples of one label and a boundary two readers
disagreed on half the time. More epochs would fit that noise harder.

**Hardware:** CPU, torch 2.15.0+cpu. 33 optimiser steps, about six minutes.
Recorded here because different hardware does the arithmetic in a different
order, and unit 6 compares numbers across seeds.

**Split sizes:** 168 train / 36 val / 36 test, stratified 70/15/15.

| Label | In the test split |
|---|---|
| `checkable` | 17 |
| `assertion` | 16 |
| `anecdote` | **3** |

`anecdote` has **3** examples in the test split, well under the 8 the notebook
warns about. Its F1 is computed on three posts, so it is not a measurement of
anything stable - one post changing hands moves it by roughly 0.33. The model
predicted `anecdote` zero times, so the figure is 0.000 regardless.

---

## How I Used AI
I used Claude for guidance and collaboration across the whole project - the
collection scripts, the labelling tool, and a long argument about what my own
labels meant. The part worth describing is the method, because it is what
produced the taxonomy I ended up with.

**The strategy: sample out, measure the direction, revise, repeat.**

I did not try to check 240 labels. I labelled small samples **blind** - Claude's
labels hidden - then measured two things against its pass: the agreement *rate*,
and more usefully the *direction* of the disagreements. A rate tells you
something is wrong. A direction tells you what. Each round, the direction named
a specific boundary, I rewrote the definition at that boundary, and the next
sample tested the rewrite.

That loop is how I learned what my labels actually mean. I designed the
taxonomy on paper and it looked fine; it only acquired real content when a
sample showed me two people applying the same written rule in opposite ways.

**Moment 1 - the first gate, and a hole in the rule**

- *What I asked for:* a taxonomy for Hacker News comments, with definitions
  precise enough to label 240 posts consistently.
- *What came back:* three labels - `anecdote` / `citation` / `assertion` - and a
  decision rule asking whether another reader could check the claim without
  taking the writer's word for it. It was convincing against the six examples it
  had been built from.
- *What I changed:* I labelled 20 posts cold and agreed with Claude on **10 of
  20**. The direction was the finding, not the rate: five of my ten
  disagreements moved a post from `assertion` into the middle label. The rule
  never said whether the *writer* had to supply the source or whether the claim
  merely had to be checkable, and we had each filled that silence differently. A
  claim like *"it is illegal to download copyrighted material"* fit none of the
  three labels cleanly, which meant the taxonomy did not cover its own space. I
  took the wider reading, renamed the label `checkable` because "citation"
  promises a reference that is usually absent, and relabelled all 240.

**Moment 2 - the second gate, and rejecting the options I was given**

- *What I asked for:* a re-labelled corpus under the new rule, and a second
  sample to test whether the rewrite had worked.
- *What came back:* **43 of 52 (83%)**, a 95% interval of 70–92%, up from 50%.
  Six of my eight disagreements still moved posts into `checkable`, so the
  residual error was systematic and one-directional rather than noise - Claude
  was still reading its own rule more narrowly than I was. It recalibrated the
  remaining 168 on that evidence. Claude then asked which of two readings of
  `anecdote` to use: lived experience, or anything in the first person, and
  predicted the second would grow the label and rescue my balance criterion.
- *What I changed:* I rejected both. An anecdote can be about anyone, told from
  any perspective - the test is whether it recounts a particular incident. That
  is the ordinary meaning of the word, and neither option offered to me
  captured it. Applying it shrank `anecdote` from about 50 posts to 17, the
  opposite of the predicted direction, and cost me criterion 3. I took the miss
  rather than bend a definition to hit a target I had set before I knew what the
  corpus looked like.

**Pre-labelling disclosure:**

Claude pre-labelled 220 of the 240 posts and re-swept them twice as the
definitions changed. I labelled 20 cold and reviewed 52 of the 220 by hand.
**168 posts, 70% of the corpus, carry a label I never individually checked.**
The `note` column in `labels.csv` marks every row with which group it belongs
to: `cold`, `pre-labelled, checked`, or `pre-labelled, unchecked`.

I am treating the sampling as a measurement rather than as a substitute for
review, and the measurement has a known limit. 83% agreement on 52 posts puts
the true rate somewhere between 70% and 92%, which is enough to say the rule is
working and not enough to call the unchecked 168 reliable. Because the residual
disagreements point one way, the likeliest error in those 168 is systematic,
too few posts called `checkable`, rather than scattered.

Claude also wrote `collect_hn.py`, `make_batch.py` and `make_label_page.py`.

---

<!-- ═══════════════════════ UNIT 6 — THE TEST ═══════════════════════

     Don't fill these in during unit 5.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Baseline vs. Trained

<!-- Both models on the same posts. `python baseline.py --trained results.json`
     prints this table for you. -->

| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy |  |  |  |
| Macro F1 |  |  |  |
| F1 — `label_one` |  |  |  |
| F1 — `label_two` |  |  |  |

**What I predicted before I looked:**
<!-- Milestone 1 asks you to write this BEFORE seeing the trained numbers. A
     prediction made afterwards isn't one. -->

**What the gap actually means:**
<!-- If the baseline matched your trained model, your fine-tuning added
     nothing — and that is a real finding, not a failure. Say it plainly. -->



---

## Run Log — Before

<!-- Five criteria across three seeds. The notebook's section 6 prints the
     spread table; the Target and Verdict columns are yours. -->

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

### Confusion matrix

<!-- ⚠️ TYPED AS A MARKDOWN TABLE. The notebook prints one ready to paste.
     An image of a matrix earns nothing. -->

| true \ predicted |  |  |  |
|---|---|---|---|
| **** |  |  |  |
| **** |  |  |  |
| **** |  |  |  |

**My biggest off-diagonal number, and what it means:**
<!-- Not "the model made mistakes" — WHICH boundary it didn't learn, and which
     direction. "7 real analysis posts were called hot_take and only 3 went the
     other way" is a direction, not just an error rate. -->



---

## Verdicts and Diagnoses

<!-- MET or MISSED against LAST UNIT's target. The target has to hold across
     all three seeds, not turn up sometimes. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**

<!-- For each miss: the cause, and how you know. The four common causes are:
     too few examples for a label, a boundary you applied inconsistently, a
     genuinely hard label pair, and a task the model can't reach from this
     much data.

     ⚠️ Use your agreement report as evidence. It is the only instrument you
     have that can tell a LABELLING problem from a MODEL problem, and this
     section is graded on whether you used it that way. -->



---

## Agreement Report

<!-- Your rate against the staff set, and every disagreement adjudicated.

     Remember you labelled these 30 under the STAFF taxonomy in
     data/staff_taxonomy.md, not your own — so every argument below is made
     from those definitions and those decision rules. -->

**Agreement rate:** ___ / 30 = ___%

<!-- Nobody grades this number. A 60% who argues every disagreement from the
     stated rules beats a 95% who wrote "staff was right" nine times. Several
     of the 30 were chosen because they're genuinely ambiguous — you should be
     winning some of these. -->

**Disagreements**

<!-- Three lines each: the post, both labels, and who you think is right and
     why — grounded in the staff definitions you were both applying.

     Then sort each into one of three piles:
       (a) the rule covered it and I applied it loosely → a consistency problem
       (b) the rule genuinely doesn't say               → a gap in the definitions
       (c) the rule is ambiguous here and my reading is defensible → argue it.
           This is a legitimate win.

     Pile (a) is the one that matters most for your diagnosis: if you applied a
     written rule two different ways on 30 posts, that is direct evidence about
     what you did across your own 200. -->

**1.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**2.**
> *The post:*
>
> *Staff said / I said:*
>
> *My call, and why:*
>
> *Which pile:*

**What the pattern in my disagreements tells me:**



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Run Log — After

| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it didn't, say so. Relabelling that didn't help is a genuinely
     interesting result and earns full credit. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped. -->



**The gap between what I meant my labels to capture and what the model
learned:**
<!-- Two sentences. Your confusion matrix is the evidence. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 5

       [ ] criteria.md has five numbered criteria, each naming a NUMBER
       [ ] Each has a reason underneath tied to your data or taxonomy
       [ ] labels.csv: at least 150 rows, text/label/note, ONE file not split
       [ ] No label above 70%
       [ ] All five unit 5 sections have real content
       [ ] Label Taxonomy includes the decision rule for your hardest boundary
       [ ] The Dataset includes three hard cases
       [ ] results.json and test_split.csv committed (the notebook does this)
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 6

       [ ] Baseline vs. Trained table, with your prediction written beforehand
       [ ] Run Log — Before, five criteria across three seeds
       [ ] Confusion matrix TYPED AS A MARKDOWN TABLE
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, using the agreement report as evidence
       [ ] Agreement Report with every disagreement adjudicated
       [ ] One improvement, with Run Log — After
       [ ] What's Still Broken
       [ ] results_three_seeds_before.json, results_three_seeds_after.json,
           baseline_results.json and
           agreement_results.json committed
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
