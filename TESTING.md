# Scaffold Testing Guide (Internal)

> This guide is for **maintainers** validating the scaffold against known third-party DApp endpoints. For developer integration instructions, see [GUIDE.md](GUIDE.md).

## Overview

Three third-party DApp test endpoints are currently supported. Each maps to a different `businessType`, exercising a different scaffold upgrade path.

- **Uniswap** · `businessType=swap` · DEX swap · simple
- **GMX** · `businessType=contract-call` · perp / LP · medium complexity
- **Morpho** · `businessType=contract-call` · lending / deposit · medium · ⚠ pre-v1.0 experimental

❌ **Not supported: 1inch** (it's an MCP-pointer skill, not a standalone Claude skill — see [GUIDE.md Appendix A](GUIDE.md#appendix-a--why-some-skills-dont-go-through-this-flow)).

## How to use this guide

1. Step 0 sets `DAPP_CHOICE` (pick one)
2. Paste subsequent code blocks into the same terminal session, in order
3. Keep the terminal open — every block shares shell environment variables
4. There's one Claude Code restart in the middle (marked ⏸)

## Step 0 — Pick a DApp test endpoint

```bash
# 📌 Pick one — edit this line only
export DAPP_CHOICE=uniswap

# The case below auto-sets the other variables
case "$DAPP_CHOICE" in
  uniswap)
    export DAPP_REPO_URL=https://github.com/Uniswap/uniswap-ai
    export DAPP_NAME=my-uniswap-swap
    export SKILL_SUBDIR=packages/plugins/uniswap-trading/skills/swap-integration
    export BUSINESS_TYPE=swap
    ;;
  gmx)
    export DAPP_REPO_URL=https://github.com/gmx-io/gmx-ai
    export DAPP_NAME=my-gmx-trading
    export SKILL_SUBDIR=skills/gmx-trading
    export BUSINESS_TYPE=contract-call
    ;;
  morpho)
    export DAPP_REPO_URL=https://github.com/morpho-org/morpho-skills
    export DAPP_NAME=my-morpho-cli
    export SKILL_SUBDIR=skills/morpho-cli
    export BUSINESS_TYPE=contract-call
    echo "⚠ Morpho repo is pre-v1.0 experimental; APIs may shift"
    ;;
  *)
    echo "❌ DAPP_CHOICE must be uniswap / gmx / morpho"
    ;;
esac

# Sanity check: print current config
echo "DAPP_CHOICE=$DAPP_CHOICE"
echo "DAPP_REPO_URL=$DAPP_REPO_URL"
echo "DAPP_NAME=$DAPP_NAME"
echo "SKILL_SUBDIR=$SKILL_SUBDIR"
echo "BUSINESS_TYPE=$BUSINESS_TYPE"
```

## Reset the test environment (run before each re-test)

```bash
# 1. Remove the scaffold (both canonical location and Claude symlink)
rm -rf ~/.agents/skills/onchainos-dapp-scaffold
rm -f  ~/.claude/skills/onchainos-dapp-scaffold

# 2. Remove the current DApp skill (both pre- and post-upgrade names)
rm -rf ~/.claude/skills/"$DAPP_NAME"
rm -rf ~/.claude/skills/"${DAPP_NAME}-onchainos"

# 3. Clean clone temp dirs for all DApps
rm -rf /tmp/uniswap-monorepo /tmp/gmx-monorepo /tmp/morpho-monorepo

# 4. Uninstall onchainOS CLI
rm -rf ~/.local/bin/onchainos
rm -rf ~/.onchainos

# 5. Clear shell env vars (keep DAPP_* for re-use)
unset ONCHAINOS_TOKEN
unset ONCHAINOS_SCAFFOLD_REPO

# 6. Sanity check
which onchainos
# Expected: onchainos not found

ls ~/.claude/skills/ | grep -E "^(onchainos-dapp-scaffold|${DAPP_NAME})"
# Expected: empty

# ⚠ After deleting skill directories, restart your AI agent — otherwise
#   the old skill registry is still cached.
```

## Part 1a — Clone the scaffold from GitHub

Scaffold repo: `https://github.com/okx/dapp-connect-agenticwallet` (MIT, public). Use `git clone` directly — no zip download needed.

```bash
# Clone the scaffold to the universal skills location
git clone https://github.com/okx/dapp-connect-agenticwallet \
  ~/.agents/skills/onchainos-dapp-scaffold

# Symlink into Claude Code's skills dir so Claude picks it up too
mkdir -p ~/.claude/skills
ln -sfn ~/.agents/skills/onchainos-dapp-scaffold \
        ~/.claude/skills/onchainos-dapp-scaffold

# Sanity check: confirm SKILL.md exists
ls ~/.agents/skills/onchainos-dapp-scaffold/SKILL.md
# Expected: SKILL.md path

# Optional: check the scaffold version
grep "^version:" ~/.agents/skills/onchainos-dapp-scaffold/SKILL.md
```

## Part 1b — Clone + copy the DApp skill

```bash
# 1. Clone to a temp directory
TMP_DIR=/tmp/"$DAPP_CHOICE"-monorepo
rm -rf "$TMP_DIR"
git clone "$DAPP_REPO_URL" "$TMP_DIR"

# 2. Copy the target skill subdirectory
cp -r "$TMP_DIR"/"$SKILL_SUBDIR" ~/.claude/skills/"$DAPP_NAME"

# 3. Safety step: rewrite the inner SKILL.md frontmatter `name`
#    to avoid colliding with an already-installed skill of the same name
sed -i.bak "s/^name: .*/name: $DAPP_NAME/" ~/.claude/skills/"$DAPP_NAME"/SKILL.md
rm ~/.claude/skills/"$DAPP_NAME"/SKILL.md.bak

# 4. Verify the directory layout
ls ~/.claude/skills/"$DAPP_NAME"/SKILL.md

# 5. Verify the frontmatter `name` was rewritten
grep "^name:" ~/.claude/skills/"$DAPP_NAME"/SKILL.md
# Expected: name: <whatever DAPP_NAME is>
```

## ⏸ Part 1 → Part 2 — Restart Claude Code

After installing the scaffold and DApp skill, Claude Code must be restarted so the skill registry picks them up. After the restart, run the command below to trigger the upgrade flow.

> The example uses `claude -p` (Claude Code's headless flag). On OpenClaw / Codex / other agents, the equivalent is to paste the trigger phrase into the agent's prompt box after restarting.

```bash
# After restarting Claude Code (headless one-shot)
claude -p "Use the scaffold to upgrade the DApp Skill at ~/.claude/skills/$DAPP_NAME, businessType=$BUSINESS_TYPE"

# Or, after restart, open the chat box and paste the command after substituting variables, e.g.:
# Use the scaffold to upgrade the DApp Skill at ~/.claude/skills/my-uniswap-swap, businessType=swap
```

## Part 2 — Verify the upgrade

```bash
# Determinism check: the upgraded skill should exist
ls ~/.claude/skills/"${DAPP_NAME}-onchainos"/SKILL.md
# Expected: SKILL.md path

# View frontmatter to confirm the spec sections were applied
grep -A3 "^name:" ~/.claude/skills/"${DAPP_NAME}-onchainos"/SKILL.md | head -10

# Optional: ask Claude to list the new skill
# claude
# Then prompt: list my local skills whose name starts with $DAPP_NAME
```

## Part 2 — Run scenario tests by businessType

Pick the DAPP_CHOICE you set, then copy the matching prompts from below. Three typical scenarios per DApp.

### Uniswap · `businessType=swap`

```bash
claude -p "Use my-uniswap-swap-onchainos to swap 100 USDC for ETH on Ethereum at 0.5% slippage"

claude -p "Use my-uniswap-swap-onchainos to quote how much USDC I can get for 1 ETH on Ethereum, quote-only no broadcast"

claude -p "Use my-uniswap-swap-onchainos to swap 0.01 WETH for USDC on Base"
```

### GMX · `businessType=contract-call` · perp futures

```bash
claude -p "Use my-gmx-trading-onchainos to open a 5x ETH long on Arbitrum with 100 USDC margin"

claude -p "Use my-gmx-trading-onchainos to fetch the current funding rate and mark price for BTC perp on Arbitrum"

claude -p "Use my-gmx-trading-onchainos to set a stop-loss at 2500 on my existing ETH long"
```

### Morpho · `businessType=contract-call` · lending

```bash
claude -p "Use my-morpho-cli-onchainos to deposit 1000 USDC into the highest-APY Morpho Blue pool on Base"

claude -p "Use my-morpho-cli-onchainos to check my Morpho positions and current health factor on Ethereum"

claude -p "Use my-morpho-cli-onchainos to borrow 500 USDC against ETH collateral on Base, target LTV 50%"
```

**Expected behavior:** the upgraded skill returns a `pending_sign` transaction object (containing `unsigned_tx` + `next_action.tool` pointing to `onchainos wallet contract-call`). The onchainOS CLI takes over from there: signing + broadcasting.
