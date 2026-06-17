---
name: find-skills
description: "Use when the user wants to find, search, browse, install, or scaffold Hermes skills. Searches the Skills Hub, suggests top matches, and creates new skills via `npx skills init` or manual SKILL.md authoring."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, discovery, search, hub, npx, init, scaffold, install]
    related_skills: [hermes-agent-skill-authoring, plan]
---

# Find Skills

## Overview

This skill covers the full lifecycle of Hermes skill discovery and creation:
browsing the Skills Hub, searching for a skill by keyword, installing from the Hub,
and scaffolding a brand-new skill (either via the interactive `npx skills init` CLI
or by authoring the `SKILL.md` file manually). Use it whenever the user asks about
finding, exploring, or adding skills to their Hermes setup.

## When to Use

| User intent | Trigger phrase examples |
|---|---|
| Find a skill for a specific task | "find a skill for X", "есть ли скилл для X" |
| Browse all available skills | "browse skills", "покажи скиллы", "list skills" |
| Install a skill from the Hub | "install skill X", "поставь скилл X" |
| Create / scaffold a new skill | "create a new skill", "init skill", "создай скилл" |
| List locally installed skills | "what skills do I have", "какие скиллы установлены" |

**Don't use for:** editing the body of an existing in-repo skill in detail — see `hermes-agent-skill-authoring` instead.

---

## Step 1 — Clarify intent

If the user's request is ambiguous, ask once:
> "Хочешь найти готовый скилл в Hub или создать новый?"

---

## Step 2A — Search / Browse the Hub

### Preferred: in-chat slash commands
```
/skills search <query>
/skills browse
/skills inspect <identifier>
```

### Alternative: Hermes CLI
```bash
hermes skills search "<query>" --limit 10
hermes skills browse
hermes skills inspect <identifier>
```

Present results as a compact table: **Name | Description | Identifier**.

After showing results offer:
> "Хочешь установить один из них? Скажи `install <identifier>`."

---

## Step 3A — Install a skill

```bash
hermes skills install <identifier>
# or inside chat:
/skills install <identifier>
```

After install, invalidate the prompt cache so the skill is available immediately:

```python
from agent.prompt_builder import clear_skills_system_prompt_cache
clear_skills_system_prompt_cache(clear_snapshot=True)
```

Tell the user: "Скилл установлен и готов к использованию в этой сессии."

---

## Step 2B — Scaffold a new skill with `npx skills init`

### 1. Check prerequisites
```bash
node --version   # need >= 20
npx --version
```

### 2. Run the interactive scaffolder
```bash
npx skills init
```

The scaffolder prompts for:
- **Skill name** — lowercase, hyphens only, e.g. `my-new-skill`
- **Description** — one line starting with "Use when ...", ≤ 1024 chars
- **Category** — e.g. `software-development`, `devops`, `research`
- **Tags** — comma-separated

It creates:
```
skills/<category>/<name>/
└── SKILL.md        ← ready-to-edit template
```

### 3. If `npx skills init` is unavailable

Fall back to creating the file manually — use the canonical template from `hermes-agent-skill-authoring`:

```markdown
---
name: <name>
description: "Use when <trigger>. <one-line behavior>."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: []
---

# <Skill Title>

## Overview
...

## When to Use
...
```

Save to: `skills/<category>/<name>/SKILL.md`

### 4. Validate frontmatter

```python
import yaml, re, pathlib
content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
assert content.startswith("---"), "Missing opening ---"
m = re.search(r'\n---\s*\n', content[3:])
fm = yaml.safe_load(content[3:m.start()+3])
assert "name" in fm and "description" in fm
assert len(fm["description"]) <= 1024
assert len(content) <= 100_000
print("OK")
```

### 5. Register and commit

```bash
hermes skills list          # verify it appears
git add skills/<category>/<name>/
git commit -m "feat(skills): add <name> skill"
```

---

## Quick-Reference Commands

| Goal | Command |
|---|---|
| Search Hub | `/skills search <query>` |
| Browse Hub | `/skills browse` |
| Inspect skill | `/skills inspect <id>` |
| Install skill | `/skills install <id>` |
| List installed | `/skills list` |
| Scaffold new | `npx skills init` |
| Publish | `/skills publish <path> --repo <owner/repo>` |

---

## Common Pitfalls

1. **`npx skills init` fails with npm cache permission error.** Fix: `sudo chown -R $(id -u):$(id -g) ~/.npm` then retry.

2. **`npx` unavailable or Node < 20.** Fall back to writing `SKILL.md` manually (see Step 2B §3).

3. **Description doesn't start with "Use when ...".** Validator allows it, but peers reject it on review. Always prefix the description with the trigger pattern.

4. **Created skill not visible in current session.** The skill loader is cached at session start. Verify with `skill_view` by path, or start a fresh session.

5. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo. Use `write_file` or the manual template for in-repo skills.

6. **Forgetting to commit.** `git add` + `git commit` is required for the skill to persist and be available to other users.

---

## Verification Checklist

- [ ] Intent clarified: search/install vs. scaffold
- [ ] Hub search results presented with Name | Description | Identifier columns
- [ ] Install confirmed with cache invalidation if installing from Hub
- [ ] For new skills: `SKILL.md` frontmatter starts at byte 0 with `---`
- [ ] `name`, `description` (≤ 1024 chars), `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Description starts with "Use when ..."
- [ ] `git add + git commit` completed for in-repo skills
- [ ] User told: "Скилл готов. Перезапусти сессию или используй `skill_view` чтобы проверить."
