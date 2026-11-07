---
name: reframe
description: Challenge the shape of a coding problem or design before building it, through five lenses (abstract, first principles, architect rewrite, day-one breaking test, dissolving abstraction), and return one recommended reframing. Use when asked to "think abstractly", "reduce to constraints", "rebuild from zero", "what would a principal architect rewrite", "what test breaks this design", "what abstraction makes this disappear", or to reframe a task before starting it.
---

# Reframe

Question the problem before solving it. Each lens below turns one prompt into a procedure with a concrete output, so the result is a changed plan, not a restatement. The lenses come from five prompts Wyrmfalls (@Wyrmfalls) posted on X on 6 Nov 2026.

`reframe` changes the shape of the solution. [`ambition`](../ambition/SKILL.md) changes the size and method of the ask (altitude, depth, range). Run `reframe` when the worry is "we are building the wrong thing or the wrong way"; run `ambition` when it is "we are asking for too little." When both apply, run `ambition` first to settle the goal, then `reframe` the design that serves it.

## When to use

- The user invokes `/code:reframe`, optionally with a lens name: `/code:reframe dissolve`.
- The user uses one of the prompts below, or close wording, about a task, plan, spec, PR, or design.
- Before starting a non-trivial build: a new module, a schema, an API, a migration, an architecture choice.

Do not run it on a well-scoped bug fix or a one-file change unless asked. Reframing a typo fix is noise.

## The lenses

| Lens | Prompt | Output |
| :- | :- | :- |
| `abstract` | "Exercise abstract thinking when considering this task." | The general class of problem and its known solutions. |
| `zero` | "Reduce this problem to its irreducible constraints and rebuild it from zero." | Hard constraints, discarded assumptions, and the minimal design they allow. |
| `architect` | "What would a principal architect immediately rewrite before even starting this?" | Ranked list of structural changes to make before line one. |
| `break` | "Design the single test that breaks this design on day one." | One concrete, runnable test and the design change it forces. |
| `dissolve` | "What higher-level abstraction would make this entire problem disappear?" | An abstraction, existing tool, or reframing under which the task stops existing. |

With a lens named, run only that lens. With none, run all five in the order above, since each feeds the next: the problem class informs the constraints, the constraints inform the rewrite, the rewrite is what the breaking test attacks, and `dissolve` asks whether any of it was needed.

## 0. Ground it

Before any lens, read what exists: the task text, the relevant code, schema, interfaces, call sites, and tests. Write the literal ask and its current plan in two lines. A lens applied to an imagined codebase produces generic advice, which is the main failure mode of this skill.

## 1. `abstract`: name the problem class

1. Strip the domain nouns. Restate the task with generic terms: "sync docket entries from PACER into our case table" becomes "incrementally replicate an append-mostly external log into a local store with an unreliable, rate-limited source."
2. Name the class: cache invalidation, change data capture, scheduling, a state machine, a graph traversal, a parser, idempotent ingestion, consensus, a search index, and so on.
3. List the standard solutions for that class and the failure modes the field already knows (for the example: cursors or watermarks, idempotency keys, backfill vs. tail, dedupe on natural key, poison messages).
4. Note which of those the current plan already handles and which it reinvents or misses.

Output: the class in one line, then a table of known solution, handled by current plan (yes, no, partly), and note.

## 2. `zero`: irreducible constraints, rebuilt

1. List every constraint the current plan assumes. Pull them from the code, the ticket, and the conversation, not from imagination.
2. Sort each into:
   - **Hard**: physics, law or regulation, a contract, an external API you cannot change, a data volume or latency number with a source. Cite the source.
   - **Soft**: inherited from the existing code, a past decision, a framework default, or habit.
3. Discard the soft constraints and design the smallest thing that satisfies only the hard ones. Describe it with concrete types, function signatures, or message shapes.
4. Add soft constraints back only when dropping one costs more than keeping it (a migration, a breaking API change, retraining users). Say which ones came back and why.

Output: the hard-constraint list with sources, the rebuilt design, and a diff against the current plan.

## 3. `architect`: what to rewrite before starting

Review the plan and the code it touches as a principal engineer would on the first read, looking for structural problems that get more expensive with every line written on top of them:

- Data model: wrong ownership, missing identity or natural key, denormalization without a reason, state that should be derived.
- Boundaries: a module or service split that forces chatty calls, or a missing seam that blocks testing.
- Contracts: public interfaces, wire formats, or schemas that will be hard to change once shipped.
- Control flow: implicit ordering, hidden global state, error handling that cannot express partial failure.
- Naming that will mislead the next reader about what a thing is.

Rank the findings by cost to change later. For each, give the change, the file and line or plan step, and what it gives up. Cap the list at five. Anything that is a style preference rather than a structural cost does not make the list.

## 4. `break`: the single day-one breaking test

1. List the design's load-bearing assumptions: input shape, ordering, uniqueness, size, timing, concurrency, failure of a dependency, clock, encoding, permissions.
2. Pick the one most likely to be false in production on the first day, given the real data and traffic. Prefer evidence (a sample of real input, a log, an API doc) over intuition, and cite it.
3. Write that test as runnable code in the repo's test framework and language, at the level where it bites (unit, integration, property, or load). Name the file it belongs in.
4. If the session can run tests, run it against the current code or a stub of the design and report the result. Otherwise say it was not run.
5. State the design change that makes the test pass.

One test, not a suite. If two candidates tie, pick the one whose failure is silent (corrupt data, wrong answer) over the one that fails loudly (crash, 500).

## 5. `dissolve`: make the problem disappear

Look for a level where the task is no longer needed:

- **Existing tool.** A library, database feature, platform service, or standard that already does this (a Postgres constraint instead of app-level dedupe, a queue's built-in retry instead of a retry loop).
- **Generalization.** One mechanism that replaces this task and its siblings (a declarative rule table instead of the fifth hand-written special case).
- **Inversion.** Change who owns the work so it vanishes here (push instead of poll, the producer validates instead of every consumer).
- **Deletion.** The feature, step, or data whose removal makes the problem moot. Check whether anything actually depends on it.

For each candidate, say what disappears, what it costs (new dependency, migration, lost flexibility, learning curve), and whether it fits the current scope or is a separate project. Recommend one, or say plainly that no abstraction beats the direct solution here. Proposing a framework to avoid writing 40 lines is a failure.

## 6. Deliver

Output, in this order:

1. **Recommended reframing.** One paragraph: the plan you would now execute and how it differs from the literal ask. If the original plan survives, say so in one sentence. That is a valid result.
2. **Lens results.** Each lens's output from above, compact.
3. **What it gives up.** Time, scope, risk, or compatibility the reframing costs versus the original plan.
4. **Open questions** that block the reframing, if any.

Then ask which plan to run through the ask-user tool (`AskUserQuestion` in Claude Code, or the app's multiple-choice equivalent): offer the original plan, the recommended reframing, and one alternative if a lens produced a real one, with the recommended option marked and a one-line reason. With no such tool, list numbered options with the recommended one first. Skip the question if the user already said to proceed, and run the recommended plan.

## Failure modes

- **Generic advice.** "Consider separation of concerns" is not a finding. Every output names a file, a type, a constraint with a source, or a runnable test.
- **Reframing for its own sake.** If the direct plan is right, say so. A recommendation to rewrite must beat the original on a stated cost.
- **Soft constraints passed off as hard.** "The existing code does X" is soft unless something external depends on X.
- **A breaking test that cannot run.** Pseudocode is not a test. Write it in the repo's framework.
- **Dissolving into a bigger project.** An abstraction that needs a quarter to build is a separate proposal, not the answer to this task. Flag it and recommend the in-scope option.
