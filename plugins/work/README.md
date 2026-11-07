# work

The knowledge-work mirror of the code workflow. Code starts from filed issues, rounds them up, delegates to coding agents, and lands reviewed PRs. Work starts from Slack, email, calendar, and meeting notes, turns them into action items, delegates to cloud sessions or a local worker, and lands outputs only after you sign off.

## Skills

| Skill | Command | Mirrors | Use when |
| :- | :- | :- | :- |
| `setup` | `/work:setup` | repo conventions | First run, or "use Linear for my tasks" |
| `intake` | `/work:intake` | filing issues | "What came in?", "What do I owe people?", start of day |
| `roundup` | `/work:roundup` | `roundup` | "What's in flight?", "What should I delegate?" |
| `projects` | `/work:projects` | `epics` | "Which projects are almost done?", "Finish or start next?" |
| `deliver` | `/work:deliver #N` | `deliver` | "Draft this here", roundup's local lane |
| `review` | `/work:review` | PR review and merge | "What's ready to send?", "Sign off" |

The loop: `intake` writes action items to the ledger. `roundup` sorts them into cloud, local, scope, human, and skip lanes and launches approved work. Cloud sessions and `deliver` end by attaching a review packet (the output, its sources, and a check report) to the item. `review` shows each packet, and only on your approval sends the email, posts the Slack reply, or shares the doc. No other skill sends anything.

## Agents

| Agent | Used by | Does |
| :- | :- | :- |
| `worker` | `deliver` | Drafts one output from the sources it is given. Marks anything it cannot source as `[UNSOURCED]`. Never sends. |
| `checker` | `deliver`, `review` | Verifies each claim against its source, plus recipients, attachments, and done-criteria. Reports PASS, FAIL, or UNVERIFIED. Read-only. |

## Setup

Run `/work:setup` once. It finds every connected tool that can hold tasks and projects (GitHub issues, Google Sheets, a Slack list, a Markdown file, or any other connected tracker), checks each with one read, and asks you to pick one and confirm how its statuses map. It then detects your sources (Slack, Gmail, Google Calendar, Granola, Google Drive) and agent backends and writes everything to `WORK.md` (default `~/.claude/WORK.md`). The other skills read the ledger from there and send you back to `setup` if it is missing. The adapter table and item, status, and packet formats are in `skills/*/references/LEDGER.md`.

The plugin also ships the [shared skills](../../shared) (`ambition`, `decide`, `style`, `tldr`, `write`) as `/work:<skill>`.

## Install

```bash
claude plugin install work@flowstack
```

**Skill only:** copy any `skills/<name>/` folder into `~/.claude/skills/`. Each carries its own copies of `LEDGER.md`, `SOURCES.md`, and `BACKENDS.md`.
