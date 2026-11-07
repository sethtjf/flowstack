# Deck mode

Slide decks: board and investor decks, QBRs, readouts, pitches, launch and sales decks, talks, and their speaker notes. A deck is an argument whose titles carry the claims and whose slides carry the evidence. This mode owns the argument, the titles, the evidence choice, and the notes. File production and visual inspection go to presentation tools.

## Contents

- [First fork: live or reading](#first-fork-live-or-reading)
- [The central argument](#the-central-argument)
- [Slide sequence](#slide-sequence)
- [Assertion headlines](#assertion-headlines)
- [Evidence](#evidence)
- [Speaker notes](#speaker-notes)
- [Layout comes after the argument](#layout-comes-after-the-argument)
- [Producing the file](#producing-the-file)
- [Editing an existing deck](#editing-an-existing-deck)
- [Checks](#checks)
- [Output](#output)

## First fork: live or reading

Decide how the deck will be consumed before anything else. The density variable is the reading condition, not the seniority of the audience.

| | Live presentation | Reading deck (slidedoc) |
| :- | :- | :- |
| Condition | Someone presents it in a room or on a call | Sent and read alone, no narrator |
| Words per slide | About 20 in the content area | About 60 to 100; past about 250, write a memo instead |
| Elements per slide | One piece of evidence | One to three |
| Where the explanation lives | The presenter's voice and the speaker notes | On the slide, in full sentences and annotations |
| Titles | Assertions | Assertions |

Infer the condition from the request ("we're presenting Thursday" is live, "send the board a pre-read" is reading). If a deck will be both presented and sent, build it for the live room and put the narration in the speaker notes, then export notes pages for the sent version, or produce a short companion memo. Never thicken live slides to make them readable alone. Ask only when the condition is unknown and the two answers would produce different decks.

## The central argument

Write one complete sentence that states the point of view and the stake before outlining: "Churn is concentrated in month-two self-serve accounts, and fixing onboarding recovers about $2M ARR." It becomes slide 1's headline or the opening of the executive summary. If it cannot be written from the sources, the analysis is not finished; say what is missing rather than building slides around a topic.

Then choose the shape:

- **Answer first** (pyramid, bottom line up front) for any deck a decision-maker reads: the conclusion, then three or four grouped supporting arguments, each with its evidence. Use this by default for board, QBR, readout, and internal decision decks.
- **Arc** for decks that must earn attention (keynotes, launch talks, some pitches): hook, context, build, insight, resolution. Use the arc within sections even in answer-first decks.

Keep observation, interpretation, and recommendation visibly separate. "Renewals fell 8% in Q3" is an observation; "pricing drove it" is an interpretation and needs its own evidence; "revert the price change" is a recommendation.

## Slide sequence

Outline the deck as titles only, in order, before any layout. Read the titles straight through.

1. Slide 1 states the central argument.
2. Each section opens with the claim it supports, then the evidence slides for it.
3. Each slide answers the question the previous slide raised.
4. The last content slide states the decision or the ask: who decides what, by when.
5. Anything that does not support a title goes to the appendix: method, full tables, backup charts.

If the titles alone do not make the argument, fix the outline. No layout rescues a broken storyline.

Common genre outlines, to adapt rather than fill in:

| Genre | Outline |
| :- | :- |
| Board or QBR | Headline result and the ask, performance against plan, what drove it, risks and what you are doing about them, decisions needed, appendix |
| Analytics readout | Answer, what we looked at and how, finding by finding (one per slide), what it means, recommendation, method and caveats |
| Investor pitch | The problem and who has it, why now, the product, evidence of traction, market, business model, team, the ask |
| Sales or customer deck | The customer's situation, what it costs them, what changes with the product, proof from similar customers, how it works, next step |
| Launch or all-hands | What is launching and why it matters, what changes for the audience, how it works, what to do now |

## Assertion headlines

Every content slide's title is a full-sentence assertion with a subject and a verb, at most two lines, about 12 words or fewer.

- "Q3 revenue grew 12% on enterprise renewals." Not "Q3 Results."
- The title states the conclusion the slide's evidence supports, not the topic of the chart.
- The title survives being read alone: on a phone, in a forwarded PDF, in an outline view.
- Section dividers, agenda, and title slides may use labels. Content slides may not.
- A headline edit to one slide stays on that slide. Check that the new title still follows from the previous slide and leads into the next, and report a break rather than rewriting neighbors.

## Evidence

- One chart, number, table, quote, or image per claim on a live slide. The evidence proves the title.
- Every number traces to data you were given, with a source line on the slide. A number-shaped hole in a layout is a gap to flag as `[NEED: ...]`, never a number to supply.
- Identify the hero slide: the one piece of evidence that is the argument. Give it the most space.
- Highlight rather than withhold: show the full series and emphasize the one that matters, so the emphasis cannot imply a conclusion the full data does not support.
- Nothing essential lives in a tooltip, hover, or animation. Direct-label the points you will mention.
- Charts that do not prove a title go to the appendix.

For chart selection and integrity, defer to a visualization skill if one is installed; otherwise check units, denominators, axis baselines, missing values, and sources directly.

## Speaker notes

For a live deck, the notes carry what the presenter says and what the audience does not need to read:

- The transition sentence into this slide and out of it.
- The exact numbers to say aloud, with their source.
- Method, sample size, and caveats that would clutter the slide.
- The likely objection and the answer.
- A timing checkpoint for long talks.

Never put the script on the slide. For a reading deck, keep notes short (sources and caveats) because the slide already carries the narration.

## Layout comes after the argument

Only once the titles and evidence are settled, assign each slide a layout archetype: full-bleed chart, chart with reasoning, comparison, small multiples, KPI row, single number, statement, table, image, or quote. Vary them: avoid three consecutive slides on the same archetype. If a slide fights its archetype, the evidence is wrong for the claim; change the evidence, not the title.

Deliver the design intent even in a markdown outline: archetype per slide, what is emphasized, what is a build step, and what is in the notes.

## Producing the file

This skill writes the content. Delegate the file and its visual check to the presentation tool available in the session, in this order of preference:

1. The user's existing deck or template (`.potx`, a branded `.pptx`, a Google Slides file): author into it so the brand and masters carry over.
2. A slides artifact type or a `pptx` skill, if the session has one.
3. Google Slides through its connector, if the deck must live there.
4. A markdown outline with a slide-by-slide spec, when nobody has asked for a file or no tool is available.

After a file is produced, inspect the rendered slides through the tool's own preview or by rendering to images (for example LibreOffice to PDF or PNG, if installed). Check that titles fit in two lines, nothing overflows or overlaps, source lines are present, and the notes landed in the notes field. Report what you could not render.

Producing a file never publishes or shares it. Uploading to a shared drive, sharing a Slides link, or sending the deck needs the user's go-ahead.

## Editing an existing deck

Read the whole deck first, including notes. Extract titles in order and read them as the argument. Then apply the job from SKILL.md:

- **Narrow edit** (one title, one slide's notes): change that unit only.
- **Substantial revision**: fix the titles-only argument first, then evidence, then notes, then layout.

Keep every supported number, label, and caveat. If a slide's number has no source in the deck or the materials, flag it rather than changing or removing it.

To lint a `.pptx`, run `scripts/lint.py deck.pptx`. It extracts slide copy and speaker notes and lints them as separate documents, because notes are spoken prose and slides are fragments; judge each by its own standard.

## Checks

1. **Titles-only read.** The titles in order make the argument with no slides.
2. **Cold reader.** Someone with no context can say what the decision or takeaway is from slide 1 and the last content slide.
3. **Evidence trace.** Every number on every slide has a source line and appears in the source material.
4. **Density.** Live slides stay near 20 words; reading slides stay under about 100.
5. **Notes.** Live decks have notes on every content slide.
6. **Variety.** No run of three identical layout archetypes.

## Output

1. One line stating the reading condition, genre, and central argument.
2. The outline: slide number, archetype, assertion title, evidence (with source), and notes.
3. The file, if one was requested and a tool produced it, with what was checked in the rendered slides.
4. A short note: assumptions, each `[NEED: ...]` gap, and slides moved to the appendix.
