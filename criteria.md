# Acceptance criteria - TakeMeter

Five criteria that say what "working" means for this classifier, written in
unit 5 **before** anything was trained.

**All five are yours this time.** None are given. You've had two projects of
practice.

An acceptance criterion names a number. *"The model is accurate"* is an
opinion. *"Every label has an F1 of at least 0.60 on the held-out set"* is a
criterion.

Under each, write a sentence or two on **why that number**. A reason that says
something about your data or your taxonomy earns credit, *"I picked 0.60 F1
for `reaction` because it's my smallest label and I only have about 50
examples of it"*. A reason that could be attached to any project does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

Not numbers that sound impressive. Three labels means a coin-flip guesser gets
about 33%, so a target of 0.40 is barely a target. Your number should sit
somewhere you'd honestly call useful.

**Cover at least three of these five areas.** They're here as prompts, not as a
form to fill in - a criterion that fits none of them is fine if it names a
number.

| Area | A question it could answer |
|---|---|
| Overall accuracy | How often does it need to be right to be worth using? |
| Per-label performance | Is one label allowed to be much worse than the others? |
| Balance | How lopsided can your label counts get before it's a problem? |
| Consistency | If someone else labelled the same posts, how often should you agree? |
| Confidence | Should a confident prediction be right more often than an unsure one? |

Two things worth knowing before you pick numbers, because both will affect
whether you hit them:

- **Your smallest label will have the jumpiest score.** If a label has 50
  examples, about 8 land in the test split. An F1 computed on 8 examples moves
  a lot between seeds. A target for that label should be looser than one for
  your biggest label, and saying so is a good reason.
- **Unit 6 tests across three seeds, and the target has to hold across all
  three.** A target of 0.65 against results of 0.71, 0.62, 0.68 is a **miss**.
  Pick with that in mind - it is stricter than it first sounds.

---

## 1. Overall accuracy of at least 0.60 on the held-out split

**Why this target:**

Criterion 3 caps my largest label at 45% of the data, so a model that ignores
the text entirely and always guesses `anecdote` scores about 0.45. 0.60 is the
first number that is clearly better than that rather than indistinguishable
from it.

I did not go higher, because criterion 3's 240 rows leave 168 for training, and
at batch 16 over 3 epochs that is roughly 30 optimizer steps. I expect an
undertrained model, and the honest target is the one I would call useful, not
the one that flatters the setup.

---

## 2. `anecdote` and `assertion` each reach an F1 of at least 0.55, and `checkable` at least 0.30

**Why this target:**

The two numbers differ on purpose. A 300-comment sample of the live feed read
roughly 39% `anecdote`, 27% `assertion` and 18% `checkable`, so `checkable` is my
smallest label even after I weight collection toward the technical threads where
it is densest.

Under criterion 3 it lands about 9 posts in the test split against 16 for
`anecdote`. One post changing hands moves an F1 computed on 9 posts by about
0.1, so holding `checkable` to the same target as the others would be measuring
which seed I drew. 0.55 where there are enough posts to hold still, 0.30 where
there are not.

---

## 3. At least 240 labelled posts, with no label above 45% and none below 25%

**Why this target:**

Three numbers doing one job: keeping every label's test split big enough to
score.

The brief's own cap is 70%, which I would clear without trying and which still
lets a majority-class guesser reach 0.70. 45% holds that guesser to 0.45, which
is what makes criterion 1 mean anything.

The 25% floor and the 240 rows are the part that costs me work. 200 rows puts
30 posts in the test split - 7 for my smallest label, under the 8 the notebook
warns about, and only 9 and 13 for the other two. 240 rows with a 25% floor
puts at least 9 in the smallest and 16 in the largest. That is 40 posts of extra
labelling to stop next unit's three-seed spread from being dominated by one post
changing hands.

Checkable before I train anything, and it cannot move between seeds.

---

## 4. I agree with the staff labels on at least 21 of the 30 posts

**Why this target:**

`data/staff_taxonomy.md` says a rate in the 70s is normal and expected on that
set, so 21/30 is the course's own stated baseline rather than a number I chose
because it was safe.

It belongs here because it is the only criterion that tests *me* rather than the
model. My hardest boundary asks whether another reader could check a claim
without taking the writer's word for it. If I cannot apply someone else's
written rule consistently across 30 posts, I have no grounds for claiming I
applied my own consistently across 240. Like criterion 3, it does not move
between seeds.

---

## 5. Mean confidence on correct predictions is at least 0.05 above mean confidence on wrong ones

**Why this target:**

`results.json` reports this directly, as `mean_when_right` and
`mean_when_wrong`.

I deliberately did not write this against `accuracy_most_confident_third`, the
other confidence number in that file. With a 36-post test split each third is
12 posts, so a gap target there shifts by about 0.08 every time one post changes
hands - it would measure the seed. The means use every post in the split.

0.05 sounds small and it is the right size. If fine-tuning on 168 examples
collapses the model toward one label, its confidence will be flat and the gap
will sit near zero. This tests whether confidence carries any information at
all, which on this much data is a genuinely open question.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 6 - read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Every label performs acceptably

         The model performs well on all labels.

         **Why this target:** ...

         > **Revised in unit 6:** Every label has an F1 of at least 0.60 on
         > the held-out set.
         >
         > **Why revised:** "performs well" gave me nothing to check. I
         > couldn't produce a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "Overall accuracy of at least 0.65" → "at least 0.55", because
            0.65 turned out to be optimistic for 200 examples.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
