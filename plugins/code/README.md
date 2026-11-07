# code

The code domain's workflow: assess epics and issues, round up everything in flight, triage, and delegate to coding agents (Claude Code cloud sessions, Devin, or a local subagent) with human review before anything lands. Building and verifying code inside a session is left to [pstack](https://github.com/cursor/plugins/tree/main/pstack). It also ships the [shared skills](../../shared) (`ambition`, `decide`, `style`, `tldr`, `write`), `parallelize` for sequential async calls on hot paths, and `mcp-audit` for MCP servers you build.

## Skills

| Skill | Command | Use when |
| :- | :- | :- |
| `epics` | `/code:epics` | "What epics are open?", "Finish or start next?" |
| `roundup` | `/code:roundup` | "Review open PRs", "What's in flight?", "Plan attack on the backlog" |
| `deliver` | `/code:deliver #N` | "Deliver #42", "Implement this here", roundup's local lane, when pstack is not in use |
| `parallelize` | `/code:parallelize [path]` | "Fix sequential awaits on hot paths", "Find await-in-a-loop", "Cut latency from serial I/O" |
| `mcp-audit` | `/code:mcp-audit [path]` | "Audit this MCP server", "Grade the server in `packages/mcp`" |
| `ambition`, `decide`, `style`, `tldr`, `write` | `/code:<skill>` | Shared with `work`; see [shared skills](../../shared) |

### roundup and epics

**`roundup`** gathers open PRs, open issues, and agent sessions on every available backend into one graph of which PR closes which issue and which session owns which PR. It proposes one plan with two verbs: **land** in-flight work (merge, close, relabel, stop orphaned sessions) and **launch** new work (a cloud session, local delivery, or a read-only scoping subagent per issue). It reads the repo's default branch, merge setup, and deployment health signal instead of assuming them, and a failed default-branch run pauses new launches. It is read-only until you approve.

**`epics`** boards every open epic, labeled or not, and sorts each into occupied, close, finish, underway, blocked, start, or park. It recommends at most three next actions, ranking leftover children of an underway epic ahead of new epics, and can write first messages for new sessions.

Both detect which agent backends the session can use (Devin through its MCP server, Claude Code cloud sessions, or a local subagent) and use only those that pass a read check. Detection rules and per-backend calls are in each skill's `references/BACKENDS.md`. Requirements: GitHub access through the GitHub MCP server or the `gh` CLI. Default labels are `epic`, `ready-for-agent`, and `ready-for-human`; other names are mapped and reported.

### deliver

**`deliver`** takes one well-scoped item to an open PR in this session. The main session plans and integrates, the `implementer` subagent writes the code, and the `test-runner` subagent runs the repo's own checks without editing. It works on a feature branch, follows the repo's commit and PR conventions, and pushes only after checks pass and you approve. In a repo set up for pstack, use `/poteto-mode` instead.

| Agent | Does |
| :- | :- |
| `implementer` | Writes the code for one delegated chunk and reports files touched and checks run. Stays in scope and never force-pushes or bypasses hooks. |
| `test-runner` | Runs the repo's lint, typecheck, build, and test commands for a scope and reports pass/fail. Read-only. |

Both run on `sonnet`. A repo's own `implementer` or `test-runner` in `.claude/agents/` wins; with neither, `deliver` uses a general-purpose subagent with the same contract.

### parallelize

**`parallelize`** maps the repo's hot paths (from traces or logs when the session can read them, else from entry points and call depth), finds independent async or blocking I/O calls that run one after another, and rewrites them to run concurrently. Each candidate must pass a nine-point safety check (data dependency, effect order, auth gates, transactions, shared state, rate limits, error semantics, context propagation, result order) before it is changed; observable behavior changes are asked about once, and the rest are reported as skipped with the failed check. Fan-outs are always bounded. Language idioms and pitfalls for TypeScript, Python, Go, Rust, Java, Kotlin, and C# are in [`skills/parallelize/references/PATTERNS.md`](skills/parallelize/references/PATTERNS.md).

### mcp-audit

**`mcp-audit`** grades an MCP server's source code against a 48-check best-practices rubric and returns a 0–100 score, a letter grade, and a list of changes, each tied to a file and line. It is read-only and never calls the server's tools. Scoring, outputs, and customization are in [`skills/mcp-audit/README.md`](skills/mcp-audit/README.md).

## Install

```bash
claude plugin marketplace add sethtjf/flowstack
```

```bash
claude plugin install code@flowstack
```

**Skill only:** copy any `skills/<skill>/` folder into `~/.claude/skills/`, `.claude/skills/`, or any agent that supports the [Agent Skills](https://agentskills.io/specification) format. Outside the plugin it runs as `/<skill>`.
