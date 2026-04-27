# Install a Third-Party DApp Skill

Use this guide if you already have a DApp skill (one you wrote, or one shared by someone else) and want to install it into your agent's skills directory before running the scaffold upgrade.

## Scenario A · Skill from GitHub

```bash
git clone <dapp-skill-repo> ~/.agents/skills/<dapp-name>
```

Example:

```bash
git clone https://github.com/my-org/my-dex ~/.agents/skills/my-dex
```

> **Claude Code users**: the installer creates a symlink at `~/.claude/skills/<dapp-name>` automatically — no extra step needed.

## Scenario B · Skill from a local directory (in development)

```bash
# Option 1: symlink (changes to source take effect immediately — recommended during development)
ln -s "$(pwd)/my-dex" ~/.agents/skills/my-dex

# Option 2: hard copy (stable, portable)
cp -r "$(pwd)/my-dex" ~/.agents/skills/my-dex
```

## Scenario C · Skill from a zip / tar archive

```bash
tar -xzf my-dex.tgz -C ~/.agents/skills/
# or
unzip my-dex.zip -d ~/.agents/skills/
```

## Post-install self-check (3 commands, ~10 seconds)

```bash
SKILL=~/.agents/skills/<dapp-name>

# 1. SKILL.md exists and YAML frontmatter is valid
python3 -c "import yaml; yaml.safe_load(open('$SKILL/SKILL.md').read().split('---',2)[1])" && echo "✓ frontmatter"

# 2. Required structure present (SKILL.md required; index.ts / README.md optional)
test -f "$SKILL/SKILL.md" && echo "✓ structure"

# 3. Agent can see the skill (restart agent if the skill name doesn't appear)
claude mcp list 2>/dev/null | grep -i "$(basename $SKILL)" || \
  echo "⚠ If the skill name doesn't appear in your agent, restart it or open a new session"
```

## Upgrade with the scaffold

Once both the DApp skill and the scaffold are installed, ask your agent:

```
Use the scaffold to upgrade ~/.agents/skills/<dapp-name>
```

The agent will automatically:
1. Read the existing skill's `SKILL.md` + `index.ts`
2. Classify each tool by business type
3. Inject `[Onchain OS dependency]` / `[signing constraint]` / `requiredTools` / Pre-flight Checks per the scaffold spec
4. Wrap transaction tools to return `pending_sign`
5. Preserve original business logic as internal helpers
6. Run self-checks and report the result
