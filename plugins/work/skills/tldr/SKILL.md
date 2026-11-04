---
name: tldr
description: Give a short, skimmable TLDR in Seth's style, either a recap of the work done (what changed, where it stands, what is next) or a refresher on why something matters. Use when asked for a "TLDR", "recap", "catch me up", "where are we", "zoom out", "what's actually going on", "remind me why this matters", or "what's the point of X".
---

# TLDR

Zoom out and tell the reader what is actually going on, in a form they can absorb in under a minute. A TLDR reports outcomes and stakes, not the steps that produced them. It follows the [`style`](../style/SKILL.md) rules; the shape below is how those rules apply to a summary.

## 1. Pick the mode

| Mode | Asked as | Answers |
| :- | :- | :- |
| Recap | "TLDR", "recap", "catch me up", "where are we", "zoom out", "what did we do" | What changed, where it stands, and what happens next. |
| Why | "Why does this matter", "remind me why", "what's the point of X", "why are we doing this" | The stake: the problem, what it costs to leave it, and what depends on it. |

If the ask names a "why", use Why. Otherwise use Recap. If both are asked ("recap this and remind me why it matters"), write the Recap and put the one-sentence stake first in the TLDR line. Do not ask which mode; pick one and go.

## 2. Pick the scope

Default to the current session or thread. Narrow it when the ask names a topic ("TLDR on the export job"), an artifact (a PR, doc, issue, or branch), or a span ("since yesterday", "this week"). For a span or an artifact outside the conversation, read it first: `git log` and `git diff` for a branch, the PR body and review threads for a PR, project memory and linked docs for a topic. Do not summarize from memory what you can check in one read.

## 3. Gather the facts

Collect only what changes the reader's picture:

- **Outcomes.** What exists now that did not before: merged PRs, files, decisions, sent messages, fixed bugs. Each with its link, path, or PR number.
- **State.** What is done and verified, what is done but unverified, what is in progress, and what is blocked and on whom.
- **Decisions.** Choices made along the way, who made them, and what each gave up. Skip choices that no longer matter.
- **Stake** (Why mode). The problem this solves, who feels it, what breaks or stays slow without it, and what is waiting on it. Prefer a number ("cuts p95 from 1.2s to 300ms", "unblocks 3 issues") when one exists. Never invent one.
- **Open items.** Unanswered questions, failing checks, pending reviews, and anything the reader owes.

Drop the process: tool calls, dead ends that left no trace, retries, and how the work was found. Keep a dead end only if it rules something out the reader might otherwise retry ("tried SQS, dropped it for IAM setup").

## 4. Write it

### Recap

```markdown
**TLDR:** <one or two sentences: the state of play, leading with the most important outcome>

**Done**
- <outcome, in the reader's terms> (<link, path, or PR>)

**Open**
- <in progress, blocked, or unverified item>: <waiting on whom or what>

**Next**
1. <concrete step the reader can take now, with link or command>
```

### Why

```markdown
**TLDR:** <one sentence: why this matters, stated as the problem it solves or the cost of not doing it>

**Why it matters:** <two to four sentences of prose: the problem, who feels it, what depends on it, and the number if there is one>

**Where it stands:** <one or two sentences: current status and the next milestone>

**Next**
1. <concrete step, if any>
```

### Rules for both

- The TLDR line alone must be enough. A reader who stops there knows the most important fact.
- Lists hold outcomes, one line each, at most five per section. Merge or cut past five; a sixth item means the scope is too wide or the items are steps, not outcomes.
- Name things in the reader's terms ("the Safari export bug"), not code or branch names, then link the artifact.
- Omit any section that would be empty. Never pad Next with invented steps.
- Mark anything you did not verify: "PR #42 is up; CI not yet checked." Do not round "pushed" up to "done."
- Keep the whole TLDR under about 150 words. If it cannot fit, the scope is too wide: give the top-level TLDR and offer the narrower recaps as one line in Next.
- No em dashes, no emoji, no exclamation points, no closing summary or offer (style rules 6, 10, and 16).

## 5. Check before sending

Reread the TLDR line and ask: if this were the only line read, would the reader know what is going on and whether they need to act? If not, rewrite it before anything else.
