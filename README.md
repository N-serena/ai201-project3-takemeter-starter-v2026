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
| Measure | Baseline | Trained | Difference |
|---|---|---|---|
| Overall accuracy | 0.389 | 0.500 | +0.111 |
| Macro F1 | 0.190 | 0.347 | +0.156 |
| F1 - `anecdote` | 0.000 | 0.000 | +0.000 |
| F1 - `checkable` | 0.571 | 0.541 | -0.031 |
| F1 - `assertion` | 0.000 | 0.500 | +0.500 |

Both columns are seed 42, scored on the same 36 held-out posts in
`test_split.csv`. `facebook/bart-large-mnli`, prompted with the definitions in
`label_definitions.txt`.

**What I predicted before I looked:**

Nothing, and I am not going to invent one. `RUNNING.md` lists two commands so
that you see the baseline alone, write a prediction, and only then reveal the
Trained column. I ran `baseline.py --trained results.json` in a single pass and
saw both columns together, so any prediction I wrote now would be written after
the fact. Milestone 1 asks for one made beforehand. I would rather lose the
point than fake it.

**What the gap actually means:**

Fine-tuning on 168 examples beat the zero-shot baseline by 11 points of
accuracy and 16 of macro F1, so it did something real. The whole of that gain
is one label: `assertion` went from 0.000 to 0.500. `checkable` got slightly
worse. `anecdote` is 0.000 in both, because neither model ever predicts it.

Two things qualify the win.

The baseline is a weak opponent. Always guessing `checkable`, the largest label
in the test split, scores 17/36 = 0.472, which beats the zero-shot model's
0.389. My trained model's 0.500 is only one post better than that trivial
guesser. Against a real baseline rather than the designated one, the
fine-tuning bought almost nothing.

And the baseline's zero on `assertion` is probably my fault rather than the
model's. The definitions are the prompt, and `assertion` is the one I wrote
negatively: *recounts no incident and rests on nothing a reader could check*. A
zero-shot entailment model scores how well a text entails each definition, and
a definition built out of absences is very hard to entail. That is a claim
about my prompt, not about the task, and it is testable: rewriting `assertion`
positively and re-running the baseline would settle it.

---

## Run Log — Before
| Criterion | Target | Seed 42 | Seed 7 | Seed 2024 | Verdict |
|---|---|---|---|---|---|
| 1. Overall accuracy | >= 0.60 | 0.500 | 0.583 | 0.667 | MISSED |
| 2. `anecdote` F1 | >= 0.55 | 0.000 | 0.000 | 0.000 | MISSED |
| 2. `assertion` F1 | >= 0.55 | 0.500 | 0.606 | 0.643 | MISSED |
| 2. `checkable` F1 | >= 0.30 | 0.541 | 0.611 | 0.732 | MET |
| 3. Every label 25-45% of 240 rows | 25-45% | 7.1 / 47.1 / 45.8 | same | same | MISSED |
| 4. Agree with staff on 21 of 30 | >= 21 | 13 | same | same | MISSED |
| 5. Confidence gap | >= 0.05 | 0.018 | 0.002 | 0.004 | MISSED |

Criteria 3 and 4 do not vary by seed: one is a fact about the dataset, the
other about me.

Macro F1 across the three seeds was 0.347, 0.406 and 0.458. Accuracy moved
**0.167** between the best and worst seed, which the notebook flags as more
than 10 points and calls a diagnosis in its own right.

That spread is the single most important number in this run log. Criterion 1's
target is 0.60. Seed 2024 returned 0.667 and would have met it. Seed 42
returned 0.500. Had I run one seed and stopped, I would have believed either
that I comfortably met the criterion or that I badly missed it, depending
entirely on the draw.

---

### Confusion matrix
Seed 42, the first of the three.

| true \ predicted | anecdote | checkable | assertion |
|---|---|---|---|
| **anecdote** | 0 | 2 | 1 |
| **checkable** | 0 | 10 | 7 |
| **assertion** | 0 | 8 | 8 |

**My biggest off-diagonal number, and what it means:**

8 real `assertion` posts were called `checkable`, against 7 real `checkable`
posts called `assertion`. That is close to symmetric, so by the notebook's own
reading the model finds the pair hard in both directions rather than leaning
one way.

The more striking feature is the column that is entirely zero. The model never
predicted `anecdote` once, on any of the three seeds. It did not learn the
label badly; it did not learn it at all, and with 17 examples in the corpus and
3 in the test split there was never much chance it would.

The symmetry matters for the diagnosis below, because my own labelling of that
same pair was *not* symmetric.

---

## Verdicts and Diagnoses
| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Overall accuracy | >= 0.60 | MISSED | 0.500 / 0.583 / 0.667. Has to hold on all three seeds; it holds on one |
| 2 | `anecdote` and `assertion` F1 >= 0.55, `checkable` >= 0.30 | see left | MISSED | `checkable` met on all three. `assertion` fails on seed 42. `anecdote` is 0.000 everywhere |
| 3 | 240 rows, every label 25-45% | 25-45% | MISSED | 7.1 / 47.1 / 45.8. Not seed-dependent |
| 4 | Agree with staff on 21 of 30 | >= 21 | MISSED | 13 of 30, or 11 of the 27 I labelled blind |
| 5 | Confidence gap >= 0.05 | >= 0.05 | MISSED | 0.018 / 0.002 / 0.004 |

**Diagnoses**

**Criterion 2, `anecdote` F1 of 0.000: too few examples for a label.** The
clearest and least interesting miss. `anecdote` is 17 of 240 posts, 3 of them
in the test split. The model predicted it zero times across three seeds. No
amount of training fixes a label the corpus barely contains.

The cause is upstream of the model. `anecdote` started at about 50 posts under
a definition that said *the writer's own experience*. When I corrected it to
what the word actually means, a particular incident recounted, 33 posts left
and the label collapsed. Hacker News comments are overwhelmingly argument and
opinion; recounted incidents are rare there. The taxonomy is sound and the
corpus cannot support it.

**Criterion 1 and the 0.167 spread: a dataset too small to measure with.** 36
test posts means one post is worth 2.8 points of accuracy. The gap between my
best and worst seed is six posts. The criterion is not so much missed as
unmeasurable at this sample size, and that applies to every per-label F1 too.

**Criterion 5, confidence gap of 0.018: the model is guessing.** Mean
confidence was 0.398 when right and 0.389 when wrong, against a 1-in-3 prior.
When I wrote this criterion I said 0.05 was the right size because *if
fine-tuning on 168 examples collapses the model toward one label, its
confidence will be flat and the gap will sit near zero*. That is what happened.
The criterion did its job: it detected a collapsed model rather than a
calibrated one.

**Criterion 4, and what the agreement report says about criteria 1 and 2: a
labelling problem, not only a model problem.**

This is the diagnosis the agreement report earns, and it points at my labels
rather than at DistilBERT.

I agreed with staff on 13 of 30, or 11 of the 27 I labelled blind. The brief
says a rate in the 70s is normal on that set. Mine is in the 40s.

Ten of my seventeen disagreements are a single pair, `hot_take` versus
`reaction`, and on that pair my labels are indistinguishable from chance: 8
right, 10 wrong, split evenly in both directions. Staff rule 2 covers that
boundary explicitly, in one sentence. I did not apply it. I read the label
names instead, taking `reaction` to mean responding to the thread and
`hot_take` to mean a heated outburst, which is why I called *"Got up at 5,
drove ninety minutes, and it's cancelled"* a `hot_take` and *"Nobody actually
enjoys the long run"* a `reaction`. Both are backwards under the written rule.

Now connect that to my own corpus. My confusion matrix confuses `checkable`
and `assertion` almost symmetrically, 8 against 7, which on its own suggests a
genuinely hard boundary. But my own labelling of that same pair was
systematically directional: six of the eight corrections I made during the
sample gate moved posts one way, into `checkable`. A hard boundary produces
symmetric model errors. A boundary where the labeller drifts one way produces
directional label noise. I have both, which means the `checkable` / `assertion`
F1 scores are measuring a mixture of a hard task and inconsistent labels, and
I cannot separate the two from the matrix alone.

The staff set is the evidence that tips it. If I can be at chance on somebody
else's explicitly written rule across 30 posts, I have no grounds for assuming
I was consistent across my own 240, of which 168 I never reviewed at all.

**What I am not claiming.** The agreement rate does not prove my own labels are
40% wrong. The staff taxonomy is not mine, and the one boundary I failed on
there, `hot_take` versus `reaction`, has no direct equivalent in my three
labels. What it does establish is that my ability to apply a written rule
consistently is much weaker than I assumed when I wrote mine.

---

## Agreement Report
**Agreement rate:** 13 / 30 = 43%

Three of the 30 are compromised: their staff labels were visible to me before I
labelled, through my own carelessness in inspecting the answer file. I agreed
on two of those three. **On the 27 I labelled blind the rate is 11 / 27 = 41%**,
and that is the number I would stand behind.

**Where the disagreements fall**

| Pair | Count |
|---|---|
| `hot_take` vs `reaction` | 10 |
| `analysis` vs `hot_take` | 4 |
| `analysis` vs `reaction` | 3 |

**Disagreements**

**Group 1, pile (a): the `hot_take` / `reaction` boundary, 10 posts.**
`sp_013`, `sp_016`, `sp_017`, `sp_019`, `sp_020` are general claims about the
world with no support offered, which staff called `hot_take` and I called
`reaction`. `sp_022`, `sp_024`, `sp_025`, `sp_029`, `sp_030` report something
that just happened to the writer, which staff called `reaction` and I called
`hot_take`.

> *Staff said / I said:* `hot_take` / `reaction` for *"Nobody actually enjoys
> the long run. They enjoy having done it."*
>
> *My call, and why:* staff are right, and it is not close. Rule 2 asks whether
> the post is about a claim or about the writer. That sentence asserts
> something general about everyone who runs. It is a `hot_take`.

> *Staff said / I said:* `reaction` / `hot_take` for *"Got up at 5, drove
> ninety minutes, and it's cancelled. Standing in the car park in the rain
> reading the email."*
>
> *My call, and why:* staff are right. Nothing general is claimed. It reports
> the writer's last hour and how it felt, which is the definition of
> `reaction`.

*Which pile:* (a) for all ten. The rule covered every one of them and I applied
it by label name instead of by definition.

**Group 2, pile (a): rule 1, 2 posts.**

> *Staff said / I said:* `hot_take` / `analysis` for `sp_014`, *"Times are down
> about 3% since the shoe rules changed, so obviously the shoes are the whole
> story and the sport has a problem."*
>
> *My call, and why:* staff are right, and this one is embarrassing. It is
> almost verbatim the worked example in `data/staff_taxonomy.md` under rule 1.
> The 3% is decoration on a conclusion already reached, and *"obviously"* and
> *"the whole story"* are the tells. A `hot_take` with a statistic in it.

`sp_023` is the other: staff `reaction`, mine `analysis`. The post contains a
comparison, *"slower than my warm-up used to be"*, but the comparison carries
no argument. The post is about not minding. Staff are right. Pile (a).

**Group 3, pile (b): where "checkable" is not defined, 3 posts.**

This is the one I would argue, and it is the same hole I found in my own
taxonomy in unit 5.

> *The posts:* `sp_005`, *"My times dropped 2% in the shoes and another 2% the
> following year in the same pair, when the only thing that changed was going
> from 35 to 50 miles a week."* `sp_007`, the same loop run in 4C and 24C.
> `sp_010`, three runners in different shoes within 10 seconds of each other.
>
> *Staff said / I said:* `analysis` for all three; I said `hot_take`,
> `reaction` and `reaction`.
>
> *My call, and why:* staff's own definition says `analysis` is *"an argument
> backed by a specific, checkable fact"*. None of these three facts is checkable
> by a reader. They are the writer's own runs, their own heart rate, their own
> training log, and nobody else can verify any of it. Compare `sp_003` (a
> scoring rule changed in 2019) and `sp_009` (a course remeasured in 2021),
> which staff also call `analysis` and which anyone can check. The staff
> taxonomy uses "checkable" to mean two different things and never says which.
>
> I do not think my labels on these three were right either. `reaction` is
> wrong under rule 3, which says recency does not outrank evidence. The honest
> position is that the staff taxonomy has no slot for an argument from personal
> data, in exactly the way mine had no slot for a verifiable claim with no
> source supplied, which is what forced me to rename `citation` to `checkable`.
>
> *Which pile:* (b). The rule genuinely does not say.

**The remaining 2 posts**, `sp_003` and `sp_009`, I called `hot_take` where
staff said `analysis`. Both state a specific public fact that carries the
argument. Staff are right, pile (a).

**What the pattern in my disagreements tells me:**

Thirteen of seventeen are pile (a), and most of those are one boundary I never
really read. That is a consistency problem, not a disagreement about meaning,
and it is direct evidence about how I labelled my own 240.

The three in pile (b) are more interesting, and they say something I did not
expect: the staff taxonomy has the same structural flaw mine did. "Checkable"
is ambiguous between *a reader can verify it* and *a specific fact is stated*,
and staff resolve it inconsistently across their own answer key. I found that
hole in my own definitions by labelling 20 posts blind and disagreeing with
myself. I found it in theirs the same way. Neither taxonomy survived contact
with 30 real posts unchanged, which is probably the most useful thing this
project has taught me.

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
