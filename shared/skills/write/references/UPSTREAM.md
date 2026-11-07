# Upstream sources

Every method in this skill was adapted, not copied wholesale, from the sources below. Each was read at the pinned revision on 7 Nov 2026. All are MIT-licensed; their notices are reproduced at the end of this file as the MIT license requires for substantial portions. No upstream file is vendored, and no upstream text is reproduced beyond short quoted rule names.

This file is named `UPSTREAM.md` rather than `SOURCES.md` because `scripts/validate.sh` requires every `references/SOURCES.md` in the repo to be identical, and the `work` plugin's skills already use that name for their input-source table.

## Sources

| Source | Path | Revision | License | Adapted into |
| :- | :- | :- | :- | :- |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | `skills/copywriting/` (v2.3.2), `skills/copy-editing/` (v2.2.1) | `96798cf38736ecdba015a1d2b0521b0c8f8f41dd` (2026-11-06) | MIT, © 2025 Corey Haines | COPY.md, EDITING.md, SKILL.md |
| [DreambaseAI/skills](https://github.com/DreambaseAI/skills) | `skills/dreambase-data-presentation/`, `skills/dreambase-data-stories/` | `5cb8671843f34e4ecb7890711d8cea949a3e0c7c` (2026-10-29) | MIT, © 2026 Dreambase | DECKS.md, NARRATIVE.md |
| [softaworks/agent-toolkit](https://github.com/softaworks/agent-toolkit) | `skills/writing-clearly-and-concisely/` | `3027f20f3181758385a1bb8c022d4041dfb4de84` (2026-03-05) | MIT, © 2026 Leonardo Flores | NARRATIVE.md |
| [blader/humanizer](https://github.com/blader/humanizer) | `SKILL.md` (v3.1.0) | `0ef9fe5bc3572734fd3ae6c448fe00a30cd5dcf0` (2026-10-28) | MIT, © 2025 Siqi Chen | EDITING.md |
| [NikhilVerma/slopsift](https://github.com/NikhilVerma/slopsift) | `skills/slopsift/SKILL.md` | `e7175fdfe4e7670a60f20ab07f53f33dd0ea7e99` (2026-11-01) | MIT, © 2026 Nikhil Verma | TOOLS.md, scripts/lint.py |
| [NikhilVerma/writinglint](https://github.com/NikhilVerma/writinglint) | `packages/slopsift/` (slopsift 0.12.0), `schema/slopsift-result-v1.schema.json` | `5e8039714d3813854db24093a2dcdded7abf1285` (2026-10-31) | MIT code, © 2026 Nikhil Verma; parser model CC BY-SA 4.0 (not used or redistributed here) | scripts/lint.py |
| [errata-ai/vale](https://github.com/errata-ai/vale) | CLI `--output=JSON` format and runtime-error objects | `66bbb85a1a78a5b5497331e04d4033357caced4d` (2026-11-07; latest tag v3.26.0) | MIT, © 2016 Joseph Kato | scripts/lint.py, assets/vale/.vale.ini |

## What was taken, and what was left

**Corey Haines, `copywriting` and `copy-editing`.** Taken: the three-way diagnosis (blank brief, real voice, point edit) that became the job table in SKILL.md; reading taste out of the input; the decompose-and-lock drafting habit; the three-question gate (picture it, prove it, swap test), extended here with a fourth test for the reader's next action; supportable claims with a named unlock and the `[NEED: ...]` marker; page section order; CTA guidance; the focused-sweep editing method (clarity, voice, so-what, prove-it, specificity, zero-risk) and the leave-it-alone test. Left: the heightened-emotion sweep as a separate pass, expert-panel scoring, headline formula catalog, content-refresh and SEO material, the product-marketing context template, and statistics quoted from other books. Haines credits the diagnosis, gate, and decompose-and-lock to Profound's `improved-copywriting` skill ([retieedra-profound/skills-marketing-library](https://github.com/retieedra-profound/skills-marketing-library), MIT); that credit carries through here.

**Dreambase, `data-presentation` and `data-stories`.** Taken: the live-versus-reading fork and its density bounds; full-sentence assertion titles and the titles-only read; the Big Idea sentence; answer-first versus arc structure; observation, interpretation, and recommendation kept separate; one claim per chart and the hero chart; highlight rather than withhold; what goes in speaker notes; layout archetypes chosen after the storyline, with variety; the cold-reader test; and delegating file mechanics to presentation tools. Left: pixel and point type scales, grids, color and brand theming, ECharts and reveal.js build paths, interactivity, accessibility specs, and the presenter canon with citations. Those belong to a presentation or visualization skill.

**Softaworks, `writing-clearly-and-concisely`.** Taken: the composition principles from Strunk's *The Elements of Style* (1918, public domain) that `style` does not already cover: paragraph per topic with a topic sentence, active voice, positive form, concrete language, needless words, related words together, emphatic words at the end, and one tense in summaries. Left: the usage and punctuation rules (covered by `style` or not needed), the full Strunk chapters, and the bundled copy of Wikipedia's "Signs of AI writing" page.

**Blader, Humanizer.** Taken: the framing that AI patterns are default choices; the ordering of structural patterns before word lists; the strong-on-one-sighting versus act-in-clusters split; the pattern families (staging, rhythm by rule, inflation, formatting by rule, chat leftovers, wrong reader), re-expressed as two compact tables; fixing from facts rather than synonyms; the fact-preservation check after shape edits; and when not to act. Left: the 26 numbered sections with their before-and-after examples, the dash rule (covered by `style` rule 6), and file and embedded modes. Humanizer's pattern catalog derives from Wikipedia's ["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup (CC BY-SA 4.0); no Wikipedia text is reproduced here.

**SlopSift and WritingLint.** Taken: running both `ai-style` and `reader-first`, error-warning-info as editorial priority, reading clusters through their components, not optimizing for zero findings, and the rule that findings are not authorship claims. The adapter reads SlopSift's v1 JSON result format. Left: `@latest` invocation through `npx` or `bunx` (it downloads), the agent stop-hook integration, and the browser demo. The adapter adds `--no-download` so the parser model is never fetched.

**Vale.** Taken: the JSON alert format (`Check`, `Severity`, `Line`, `Span`, `Match`, `Message`) and the runtime-error object (`Code`, `Text`) Vale writes to stderr, including `E100` for a missing config. Left: `vale sync` and packaged styles, which download; users add those to their own `.vale.ini`.

## Updating a source

To pull in a newer upstream revision: read the upstream diff since the pinned commit, adapt what changed in this skill's own words, update the revision and date in the table, and run `python3 scripts/test_lint.py` if the SlopSift or Vale output format changed.

## License notices

Each source is distributed under the MIT License with the copyright line shown below:

- Copyright (c) 2025 Corey Haines
- Copyright (c) 2026 Dreambase
- Copyright (c) 2026 Leonardo Flores
- Copyright (c) 2025 Siqi Chen
- Copyright (c) 2026 Nikhil Verma
- Copyright (c) 2016 Joseph Kato

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
