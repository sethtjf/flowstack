# flowstack

Seth's personal [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugins/create-marketplace). The marketplace is named `flowstack`, so you add `sethtjf/flowstack` and install `<plugin>@flowstack`. Plugins are grouped into two domains, code and work, mirroring how Claude and ChatGPT keep code and work as separate areas of their apps. `code` and `work` are for doing tasks, and each ships the five domain-neutral [shared skills](shared) (`ambition`, `decide`, `style`, `tldr`, `write`), so each harness needs only its own plugin. A third plugin, `reflect`, is for improving the setup itself from session history.

## Install

Add the marketplace once, then install plugins from it:

```bash
claude plugin marketplace add sethtjf/flowstack
```

```bash
claude plugin install <plugin>@flowstack
```

On Claude Code 2.1.275 or later, one command inside a session does both:

```
/plugin install <plugin> --marketplace sethtjf/flowstack
```

## Plugins

| Domain | Plugin | Description | Slash commands |
| :- | :- | :- | :- |
| code | [`code`](plugins/code) | Board epics, round up PRs, issues, and agent sessions into one land-and-launch plan, deliver an item locally, parallelize sequential async calls on hot paths, reframe a problem or design before building it, and audit MCP servers you build. Pairs with [pstack](https://github.com/cursor/plugins/tree/main/pstack) for building and verifying code. | `/code:epics`, `/code:roundup`, `/code:deliver`, `/code:parallelize`, `/code:reframe`, `/code:mcp-audit` |
| work | [`work`](plugins/work) | Set up a task tool of your choice, turn Slack, email, calendar, and meeting notes into action items, delegate them to cloud sessions or a local worker, and sign off on every outward send. | `/work:setup`, `/work:intake`, `/work:roundup`, `/work:projects`, `/work:deliver`, `/work:review` |
| both | [shared skills](shared) | Frame a task, settle open questions with a recommended option, write in Seth's style, get a TLDR recap or why-it-matters refresher, and compose or edit website copy, decks, and narrative. Shipped in `code` and `work` from one source in `shared/skills/`. | `/code:ambition` or `/work:ambition`, and likewise `decide`, `style`, `tldr`, `write` |
| reflect | [`reflect`](plugins/reflect) | Review past chats and sessions, find patterns, and interview you until you can name what to change in your setup. | `/reflect:introspect` |

Plugin skills run as `/<plugin-name>:<skill-name>`.

## Update

Pull the latest marketplace listing and any plugin whose `version` changed:

```bash
claude plugin marketplace update flowstack
```

Auto-update is off by default for third-party marketplaces. Turn it on in `/plugin` under **Marketplaces**, select `flowstack`, then **Enable auto-update**.

## ChatGPT and Codex

The same plugins install in OpenAI's Codex (CLI, IDE, and desktop app) and the ChatGPT desktop app, from the same `skills/` folders. OpenAI reads `.agents/plugins/marketplace.json` and each plugin's root `plugin.json`, in the portable [Agent Plugins format](https://developers.openai.com/plugins/build/plugins.md). Both are generated from the `.claude-plugin/` manifests by `scripts/build-openai.py`, so never edit them by hand. Add the marketplace:

```bash
codex plugin marketplace add sethtjf/flowstack
```

Then install `code`, `work`, or `reflect` from the plugin directory in Codex or the ChatGPT desktop app, and restart the desktop app to pick up changes. To share a plugin with a ChatGPT workspace, a workspace admin publishes it from ChatGPT Plugins, Personal tab ([docs](https://developers.openai.com/codex/plugins/build.md)). In Codex a skill runs as `$<skill>` and in ChatGPT as `@<skill>`, not `/<plugin>:<skill>`. `work` sets `setup` as its onboarding skill, so ChatGPT and Codex run it after install.

Not everything carries over:

| Claude feature | On ChatGPT and Codex |
| :- | :- |
| Subagents in `agents/` (`implementer`, `test-runner`, `worker`, `checker`) | No plugin equivalent; the folders are ignored. `/code:deliver` and `/work:deliver` delegate to them, so expect the model to do that work inline. Untested. |
| `AskUserQuestion` in `ambition`, `decide`, `style`, and `write` | Not available. Each skill already falls back to numbered options with the recommended one first. |
| `~/.claude/` paths | `/reflect:introspect` reads Claude Code session history in `~/.claude/projects/`, which Codex does not write, so it finds nothing to review there. `work` falls back from `~/.claude/WORK.md` to `$WORK_MD` or `./WORK.md`. |
| Scripts in skills (`write`'s optional `scripts/lint.py`, `mcp-audit`'s scorers) | Run only where the agent has a shell and python3, as in Codex. `lint.py` also needs SlopSift or Vale installed locally and reports them as missing otherwise. Untested in ChatGPT. |
| MCP servers | No plugin bundles one today, so nothing to translate. A future bundled server needs a root `mcp.json` with a transport `type`, and public listing needs a remote HTTPS endpoint. |
| Hooks | None shipped. OpenAI runs plugin hooks only for manual installs in the Codex desktop app. |

## Using a skill without the plugin

Each `plugins/<name>/skills/<skill>/` folder is also a standalone [Agent Skill](https://agentskills.io/specification). Copy it into `~/.claude/skills/` to use it in Claude Code without installing the plugin, or into any agent that supports the Agent Skills format. Outside a plugin the skill runs as `/<skill>` with no plugin prefix.

## Repo layout

```
.claude-plugin/marketplace.json   marketplace manifest (name: flowstack)
.agents/plugins/marketplace.json  ChatGPT and Codex marketplace (generated)
plugins/code, work, reflect       the three plugins; plugin.json at each root is generated for OpenAI
shared/skills/                    the one editable copy of the shared skills
scripts/sync-shared.sh            copies shared/skills/ into both plugins
scripts/build-openai.py           writes the OpenAI manifests from the .claude-plugin ones
scripts/validate.sh               validation, also run in CI; fails if a copy or OpenAI manifest drifts
.github/workflows/validate.yml    runs validate.sh on push and PRs
```


To change a shared skill, edit `shared/skills/<skill>/` and run `scripts/sync-shared.sh`; never edit the copies under `plugins/`. Upgrading from the old plugin names? See [Migrating from older plugins](#migrating-from-older-plugins). To add or update a plugin, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Migrating from older plugins

The marketplace was renamed from `sethtjf` to `flowstack` (repo `sethtjf/flowstack`, formerly `sethtjf/plugins`). `workflow` and `mcp-servers` became `code`. `style`, `decide`, and `ambition` now ship inside both `code` and `work`, and `introspect` moved to `reflect`. Reinstall once per machine:

```bash
claude plugin marketplace remove sethtjf
claude plugin marketplace add sethtjf/flowstack
claude plugin install code@flowstack
claude plugin install work@flowstack
claude plugin install reflect@flowstack
```

Removing the `sethtjf` marketplace also removes every plugin installed from it (`writing`, `thinking`, `workflow`, `mcp-servers`, `flow`, or the new names). If you added the short-lived `flow` marketplace, remove it too: `claude plugin marketplace remove flow`. Then replace any `@sethtjf` keys in `settings.json` (`enabledPlugins`) and dotfiles.

| Old command | New command |
| :- | :- |
| `/writing:style` | `/code:style` or `/work:style` |
| `/writing:open-questions` | `/code:decide` or `/work:decide` |
| `/thinking:ambition` | `/code:ambition` or `/work:ambition` |
| `/thinking:introspect` | `/reflect:introspect` |
| `/workflow:roundup` | `/code:roundup` |
| `/workflow:epics` | `/code:epics` |
| `/workflow:deliver` | `/code:deliver` |
| `/mcp-servers:audit` | `/code:mcp-audit` |

## License

[MIT](LICENSE). Each plugin declares its own `license` in `plugin.json`.
