# Tools

`scripts/lint.py` runs SlopSift and Vale over a draft and returns their findings in one shape. Linting is optional. Run it when the user asks for a lint, or before delivering a substantial piece when a tool is already installed. Never install a tool, add a dependency, or add a hook to make it run.

## Contents

- [What it runs](#what-it-runs)
- [Setup](#setup)
- [Supported inputs](#supported-inputs)
- [Running it](#running-it)
- [Output](#output)
- [Interpreting findings](#interpreting-findings)
- [Limits](#limits)

## What it runs

| Tool | Finds | How it is located |
| :- | :- | :- |
| [SlopSift](https://slopsift.dev) | Structural AI-writing patterns (`ai-style` rulepack) and hard-to-follow sentences (`reader-first`), from a local dependency parser | `$SLOPSIFT_BIN`, then `node_modules/.bin/slopsift` in the current or a parent directory, then `slopsift` on `PATH` |
| [Vale](https://vale.sh) | Rule-based style checks: repetition, and whatever styles the project's `.vale.ini` enables (Google, Microsoft, write-good, a house style) | `$VALE_BIN`, then `vale` on `PATH` |

The adapter never calls `npx`, `bunx`, `vale sync`, or a package manager. It passes SlopSift `--no-download`, so a missing parser model is a failure, not a fetch. Nothing is sent to a hosted service.

## Setup

These are for the user to run, once, if they want linting. Do not run them on the user's behalf without being asked.

```bash
npm install --save-dev slopsift      # per project; needs Node.js 24 or newer
npm install --global slopsift        # or once per machine
```

```bash
brew install vale                    # macOS; other platforms: https://vale.sh/docs/install
```

Vale needs a config to do more than its built-in checks. If the project has a `.vale.ini`, the adapter uses it. If Vale finds none, the adapter falls back to `assets/vale/.vale.ini`, which enables only Vale's built-in style with spelling off. To use packaged styles, the user adds them to a project `.vale.ini` and runs `vale sync` themselves.

## Supported inputs

| Input | Linted as |
| :- | :- |
| `.md`, `.mdx`, `.markdown`, `.txt`, `.text`, `.rst`, `.adoc`, `.html`, `.htm` | The file as-is |
| `.pptx` | Two documents: slide copy (`part: slides`) and speaker notes (`part: notes`), each finding tagged with its slide number |
| `.docx` | Body paragraphs (`part: body`) |
| `-` | Text read from stdin |

Anything else (PDF, Keynote, Google Slides, a live URL) is a usage error. Export the text to `.md` or `.txt` first: for Google Slides, export the deck to `.pptx`; for a web page, save the copy you are editing, not the rendered HTML with navigation.

For short text not already in a file, pipe it on stdin rather than writing into the user's files.

## Running it

From this skill's folder, or with the full path to `scripts/lint.py`:

```bash
python3 scripts/lint.py draft.md                       # both tools, JSON
python3 scripts/lint.py draft.md --format text         # readable summary
python3 scripts/lint.py deck.pptx --level warning      # skip info-level findings
python3 scripts/lint.py page.md --tool vale --vale-config path/to/.vale.ini
```

Exit codes: `0` clean, `1` findings, `2` incomplete (a requested tool was missing or failed), `64` usage error. Exit `2` is never a clean result, even with zero findings.

`python3 scripts/test_lint.py` exercises the clean, findings, missing-tool, and failure paths with fake binaries.

## Output

```json
{
  "schema": "write-lint/1",
  "status": "findings",
  "summary": {"findings": 1, "by_severity": {"error": 0, "warning": 1, "info": 0}, "documents": 2},
  "documents": [
    {"file": "deck.pptx", "part": "slides", "extracted": true},
    {"file": "deck.pptx", "part": "notes", "extracted": true}
  ],
  "tools": [
    {"tool": "slopsift", "status": "ok", "version": "0.12.0", "exit_code": 0, "command": ["..."]},
    {"tool": "vale", "status": "missing", "note": "Install it yourself if you want it..."}
  ],
  "findings": [
    {
      "file": "deck.pptx",
      "part": "notes",
      "location": {"line": 1, "column": 16, "end_line": 1, "end_column": 30, "slide": 1},
      "tool": "slopsift",
      "rule": "ai-style/promo-idioms",
      "severity": "warning",
      "message": "Promotional / marketing tone. Prefer plain, neutral phrasing.",
      "text": "groundbreaking",
      "original": {"ruleId": "ai-style/promo-idioms", "level": "warn", "confidence": "medium"}
    }
  ]
}
```

`severity` is normalized to `error`, `warning`, or `info` (SlopSift `warn` becomes `warning`; Vale `suggestion` becomes `info`). `original` holds the tool's diagnostic unchanged, including SlopSift's `confidence` and `ruleUrl` and Vale's `Span` and `Action`. A tool entry with `status: failed` carries its `exit_code`, `stderr`, and `error`.

## Interpreting findings

- **Errors first.** SlopSift errors are narrow, high-confidence signatures; fix them unless the author's voice uses the construction on purpose.
- **Warnings in context.** Read the sentence around the range. Apply the pattern guidance in [EDITING.md](EDITING.md#recurring-ai-writing-patterns), including when not to act.
- **Info as weak signals.** A single passive, em dash, or familiar word can be correct. Act on clusters, not singletons.
- **Clusters.** For a SlopSift `evidence-cluster` finding, read the component findings in the same range and fix the sentence from its facts.
- **Slides and notes differ.** Slide copy is fragments and assertion titles; reader-first findings about sentence completeness may not apply to a label slide. Notes are spoken prose and should read aloud.
- **Do not chase zero.** Rewriting to silence a rule can strip facts or voice. Leave a finding when the text is right, and say why in the note to the user.
- **Not authorship.** Findings are editorial signals. Never describe a document or a person's writing as AI-generated on the basis of lint output.

Report findings to the user as: the rule, the exact text, and a one-line direction, strongest first. Re-run the same command after edits and report what remains.

## Limits

- SlopSift's rules target English prose. It reads Markdown table rows as run-on sentences, so tables draw `reader-first/sentence-load` and `fragment-chain` findings that rarely need action.
- A project `.vale.ini` whose sections match specific paths (`[docs/*.md]`) will not match extracted `.pptx` or `.docx` text, which is written to a temporary `.md` file; pass `--vale-config` with a `[*.md]` section to lint those.
- `.pptx` extraction reads text runs in shape order; text inside charts, SmartArt, and images is not extracted.
- Slides are linted as one document so cross-slide rules still work. A paragraph-scale finding can span two adjacent slides; its `slide` is the slide where it starts.
- Raw finding counts grow with length and are not a quality score.
