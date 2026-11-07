---
name: write
description: Compose or edit substantive writing in one of three modes, website copy, decks, or general narrative (memos, essays, reports, posts), by establishing audience, purpose, evidence, and scope first and keeping every supported fact. Use when asked to write, rewrite, tighten, or review a web page, landing page, headline, CTA, slide deck, slide titles, speaker notes, memo, essay, article, or report, or for "/write copy", "/write deck", or "/write narrative". Not for ordinary chat replies.
argument-hint: "[copy | deck | narrative] [brief, draft, file path, or sources]"
compatibility: Optional linting needs a locally installed SlopSift (Node.js) or Vale CLI and python3 3.9+. Nothing is downloaded.
---

# Write

Compose and edit writing that has a reader, a purpose, and evidence behind it. This skill supplies method: how to build a page argument, a deck storyline, or an essay, and how to edit one without breaking it. Sentence-level rules come from the [`style`](../style/SKILL.md) skill, which stays authoritative for Seth's preferences; this skill does not restate them.

## When this skill applies

Use it for a deliverable someone will read outside this conversation: a web page or section of one, a deck or its titles and notes, a memo, essay, report, post, or a narrow edit to any of these. Do not run the workflow on an ordinary chat reply, a commit message, or a code comment. Those follow `style` alone.

## Precedence

1. What the user asks for in the conversation (a length, a format, a word).
2. For text in someone else's voice (a brand's page, an author's draft): their brand guide, voice samples, and existing draft. `style` exempts text written in someone else's voice, so do not impose Seth's rules on a client's copy.
3. `style`, for anything in Seth's voice and for every note, annotation, and summary you write to the user. If `style` is not installed, use the user's own writing preferences.
4. This skill's defaults.

## 1. Pick the mode

| Mode | Asked as | Reference |
| :- | :- | :- |
| `copy` | Web page, landing page, homepage, pricing, feature page, hero, headline, subhead, CTA, tagline, value proposition | [references/COPY.md](references/COPY.md) |
| `deck` | Deck, slides, presentation, pitch, board or QBR deck, slide titles, speaker notes, readout | [references/DECKS.md](references/DECKS.md) |
| `narrative` | Memo, essay, article, blog post, report, op-ed, explainer, brief, cover note, long email | [references/NARRATIVE.md](references/NARRATIVE.md) |

If the first argument is `copy`, `deck`, or `narrative`, use that mode. Otherwise pick from the request and the input: a URL or HTML file suggests `copy`, a `.pptx`, Google Slides link, or slide outline suggests `deck`, and anything else is `narrative`. State the mode in one line and continue. Ask only when two modes would produce materially different deliverables, such as "turn this into something for the board" (memo or deck).

## 2. Pick the job

| Job | Signal | Scope of change |
| :- | :- | :- |
| New draft | A brief, sources, or a one-line ask; no draft, or a draft with no usable argument | Build the argument from the sources. Latitude on angle and structure, none on facts. |
| Substantial revision | A draft with a real argument or voice, and a request to rework, restructure, or "make it better" | Keep the author's argument, emphasis, and vocabulary. Fix structure, buried leads, vague claims, and patterns. |
| Narrow edit | "Fix this headline", "tighten this paragraph", "rewrite slide 4's title" | Change only the named unit, plus the minimum around it needed to fit. Return the rest untouched. |

A headline edit stays a headline edit. Do not rewrite the subhead, add sections, or run a full editorial pass because you noticed other problems. If they matter, list them in one line after the edit. Infer the job from what the user gave you and asked for, and state it in one line with the evidence ("narrow edit: asked to fix the hero headline only").

For every revision and narrow edit, load [references/EDITING.md](references/EDITING.md).

## 3. Read before asking

Before any question, read what exists: product or brand context (`.agents/product-marketing.md`, `.claude/product-marketing.md`, a brand guide, `design.md`, the live site), the existing draft or deck, source documents, prior versions, and any voice sample the user supplied. Search the repo or the attached files for these; do not ask for something you can find.

Then establish four things. Write them as one short block before drafting a new piece or a substantial revision; skip the block for a narrow edit.

```markdown
Audience: <who reads it, what they already know, what they doubt>
Purpose: <the one thing the reader should do, decide, or believe after reading>
Evidence: <the facts, numbers, quotes, and proof available, each with its source>
Scope: <the deliverable, its length or slide count, and what is out of scope>
```

Infer a reasonable default for each and say which you inferred. Ask only when a missing answer would change the result materially (the reading condition of a deck, which product is being sold, who the decision-maker is). Ask through the ask-user tool with a recommended option, per `style` rule 4.

## 4. Evidence rules

These hold in every mode and every job.

- Never invent a statistic, testimonial, customer name, logo, quote, result, date, or citation. When a claim needs proof you do not have, write the closest claim the sources support and mark the gap inline as `[NEED: <the evidence that would support the stronger claim>]`.
- Preserve every supported fact, number, name, technical distinction, and stated uncertainty. A hedge in the source that reflects real uncertainty stays. A distinction the author drew (accepted vs. pending, p50 vs. p95, holding vs. dicta) stays drawn.
- Keep the author's voice: their vocabulary, sentence length, and register. "Stuff" does not become "solutions."
- Report each gap you flagged in the note to the user, so the missing evidence becomes an action item.

## 5. Draft or edit

Follow the mode reference for structure. For revisions and narrow edits, follow [references/EDITING.md](references/EDITING.md) for passes and the fact check. Work in units (a headline, a slide, a paragraph), lock each unit that works, and assemble once.

## 6. Check

1. Run the mode reference's own test (the copy gate, the deck titles-only read, or the narrative outline read).
2. Run the fact check in [EDITING.md](references/EDITING.md#fact-check): every fact in the output traces to a source, and every supported fact in the input survives or was cut on purpose.
3. Optional: run the linter (below).

## 7. Deliver

Return the deliverable, then a short note to the user in `style`: the mode and job, assumptions you made, each `[NEED: ...]` gap, and any lint findings you chose to keep. For a narrow edit, return only the changed unit and one line of reason.

Drafting never publishes, sends, shares, or deploys. Write to a file, a draft, or the chat. Committing to a branch is fine when the user asked for file changes; pushing to a live site, sending an email, sharing a doc, or publishing a page needs the user's explicit go-ahead in this conversation. In `work`, outward sends go through `/work:review`.

## Optional linting

Run `scripts/lint.py` only when the user asks for a lint, or when you are delivering a substantial piece and SlopSift or Vale is already installed. It uses only tools already on the machine, never downloads anything, and reports a missing tool as missing, not as a clean result. Findings are editorial signals, not proof of AI authorship. See [references/TOOLS.md](references/TOOLS.md).

```bash
python3 scripts/lint.py draft.md
python3 scripts/lint.py deck.pptx    # slide copy and speaker notes linted separately
```

## Sources

The methods are adapted from Corey Haines's `copywriting` and `copy-editing`, Dreambase's `data-stories` and `data-presentation`, Softaworks's `writing-clearly-and-concisely`, Blader's Humanizer, SlopSift, and Vale, all MIT. Pinned revisions, licenses, and what was taken from each are in [references/UPSTREAM.md](references/UPSTREAM.md).
