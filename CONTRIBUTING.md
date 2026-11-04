# Adding or updating a plugin

Each plugin lives in `plugins/<name>/` and has one entry in `.claude-plugin/marketplace.json`. `scripts/validate.sh` checks that the two agree. CI runs the same script on every push and pull request.

## Add a plugin

1. **Unzip into `plugins/<name>/`.** Afterwards `plugins/<name>/.claude-plugin/plugin.json` must exist. If the zip has a wrapping folder (`plugins/<name>/<name>/.claude-plugin/...`), flatten it:

   ```bash
   unzip ~/Downloads/<name>.zip -d plugins/<name>
   ```

   ```bash
   ls plugins/<name>/.claude-plugin/plugin.json
   ```

2. **Set `license` and `version` in `plugin.json`.** Use `"license": "MIT"` to match the repo unless the plugin needs something else. Start at `"version": "0.1.0"` or keep the version the plugin shipped with.

3. **Add the marketplace entry** to the `plugins` array in `.claude-plugin/marketplace.json`:

   ```json
   { "name": "<name>", "source": "./plugins/<name>", "description": "One sentence on what it does." }
   ```

   - `name` must equal `name` in `plugins/<name>/.claude-plugin/plugin.json`. A mismatch fails at install with "Plugin not found in marketplace."
   - `source` is relative to the repo root, starts with `./`, and has no `..`.
   - Do not put `version` here. Keep it only in `plugin.json`.

4. **Add OpenAI settings and generate the ChatGPT and Codex manifests.** Add an entry for `<name>` to `OPENAI` in `scripts/build-openai.py` (`displayName`, `category`, and optionally `onboardingSkill`), then run it:

   ```bash
   scripts/build-openai.py
   ```

5. **Validate:**

   ```bash
   scripts/validate.sh
   ```

6. **Add a row to the Plugins table in `README.md`:** name, description, and slash command (`/<name>:<skill>` for each skill).

7. **Commit and open a PR.** When it merges to `main`, the `tag-releases` workflow creates a `<name>--v<version>` tag and a GitHub release for the new plugin. You don't run `claude plugin tag` by hand. `validate.yml` has already checked that `plugin.json` and the marketplace entry agree.

## Update a plugin

1. Make the change under `plugins/<name>/`.
2. **Bump `version` in `.claude-plugin/plugin.json`.** Installed users keep their cached copy until the version string changes, so an unbumped change never reaches them.
3. Run `scripts/build-openai.py` to regenerate the ChatGPT and Codex manifests (`plugins/<name>/plugin.json` and `.agents/plugins/marketplace.json`), then `scripts/validate.sh`. Update the README row if the description or commands changed, and commit. The merge to `main` tags and releases the new version.

## Update a shared skill

`ambition`, `decide`, `style`, and `tldr` ship in both `code` and `work`. Edit them only in `shared/skills/<skill>/`, then copy them into both plugins and bump both versions:

```bash
scripts/sync-shared.sh
```

`scripts/validate.sh` fails if `plugins/code/skills/<skill>/` or `plugins/work/skills/<skill>/` differs from the source.

## Rules the validator enforces

| Rule | Why |
| :- | :- |
| Every `source` directory exists | `claude plugin validate` passes a missing directory. Install then fails with `Source path does not exist`. |
| Entry `name` equals `plugin.json` `name` | Otherwise install fails with "Plugin not found in marketplace." |
| `source` starts with `./`, no `..` | Relative sources resolve from the repo root and cannot leave it. |
| Every `plugins/*` directory has an entry | Catches a plugin that was unzipped but never listed. |
| `license` and `version` set in `plugin.json` | Anthropic's plugin directory rejects plugins without a license. Version drives updates. |
| No `version` in the marketplace entry | When both are set, `plugin.json` wins without warning. |
| Skill `name` matches its folder, lowercase letters, digits, and single hyphens, at most 64 chars | [Agent Skills spec](https://agentskills.io/specification). |
| Shared skill copies match `shared/skills/` | One source, two plugins, no drift. |
| OpenAI manifests match `scripts/build-openai.py` output and the Agent Plugins schema's top-level keys | They are generated, so a hand edit or a skipped regeneration would ship stale metadata to ChatGPT and Codex. |
| Marketplace name is not reserved | `claude plugin marketplace add` refuses official Anthropic names such as `claude-plugins-official`. |

## Test an install locally

From the repo root:

```bash
claude plugin marketplace add ./
```

```bash
claude plugin install <name>@flowstack
```

A marketplace added from a local path loads plugin files in place, so edits show up at the next session start or after `/reload-plugins` without a version bump. Remove it with `claude plugin marketplace remove flowstack` before adding the GitHub copy.
