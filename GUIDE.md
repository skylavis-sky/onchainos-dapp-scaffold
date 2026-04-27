# Scaffold Testing Guide

## Overview

Three third-party DApp test endpoints are currently supported. Each maps to a different `businessType`, exercising a different scaffold upgrade path.

- **Uniswap** · `businessType=swap` · DEX swap · simple
- **GMX** · `businessType=contract-call` · perp / LP · medium complexity
- **Morpho** · `businessType=contract-call` · lending / deposit · medium · ⚠ pre-v1.0 experimental

❌ **Not supported: 1inch** (it's an MCP-pointer skill, not a standalone Claude skill — see Appendix A).

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

> **After repo migration**, swap the URL below for `https://github.com/okx/dapp-connect-agenticwallet`.

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

## Appendix A — Why 1inch doesn't go through this flow

The `1inch/1inch-ai` repo's `skills/1inch-mcp-server/SKILL.md` is an **MCP-pointer skill** that points to the remote `https://api.1inch.com/mcp/protocol` service. It has no local `index.ts` to upgrade, requires a 1inch Business Portal API key, and runs all signing logic on a remote server.

The scaffold's upgrade flow targets local skills with `pending_sign`-shaped functions; the architectures don't match. Use 1inch directly as an MCP server instead — don't run it through the scaffold.

## Appendix B — EIP-712 structure conversion (Uniswap walkthrough)

> When third-party DApp APIs return a non-standard EIP-712 structure (e.g. Uniswap Trading API's `permitData`), you must convert before passing to `onchainos wallet sign-message`.

### The problem

Uniswap Trading API returns `permitData` in this shape:

```json
{
  "domain": { "name": "Permit2", "chainId": 1, "verifyingContract": "0x000..." },
  "types":  { "PermitSingle": [...], "TokenPermissions": [...] },
  "values": { "details": {...}, "spender": "0x...", "sigDeadline": "1234567890" }
}
```

But `onchainos wallet sign-message --type eip712` requires the standard EIP-712 shape:

```json
{
  "types":       { "EIP712Domain": [...], "PermitSingle": [...], "TokenPermissions": [...] },
  "primaryType": "PermitSingle",
  "domain":      { "name": "Permit2", "chainId": 1, "verifyingContract": "0x000..." },
  "message":     { "details": {...}, "spender": "0x...", "sigDeadline": "1234567890" }
}
```

Sending without conversion fails with `missing msgHash` (misleading — the actual issue is structural).

### `jq` conversion

```bash
PERMIT_DATA='<permitData JSON string from the API>'

TYPED_DATA=$(echo "$PERMIT_DATA" | jq '{
  types: (
    { EIP712Domain: [
        { name: "name",              type: "string"  },
        { name: "chainId",           type: "uint256" },
        { name: "verifyingContract", type: "address" }
      ]
    } + .types
  ),
  primaryType: (.types | keys | map(select(. != "EIP712Domain")) | first),
  domain:      .domain,
  message:     .values
}')

onchainos wallet sign-message \
  --type eip712 \
  --message "$TYPED_DATA" \
  --from <YOUR_WALLET_ADDRESS> \
  --chain eip155:1
```

### Conversion rule of thumb

| Original field | Standard field | Notes |
|----------------|----------------|-------|
| `values` | `message` | Direct rename |
| `types` | `types` (merge) | Add the `EIP712Domain` type definition |
| `domain` | `domain` | Pass through |
| (missing) `primaryType` | `primaryType` | First key in `types` excluding `EIP712Domain` |

### Scaffold injection rule (v1.3)

In the routing-conversion section, when the scanner detects this pattern, the scaffold **must** auto-inject a reference to this appendix:

```
- API returns a field named `permitData` / `typedData` / `signatureData`
- AND code uses `walletClient.signTypedData` / `signTypedData(...)` / `eth_signTypedData_v4`
```

---

## Appendix C — EIP-712 numeric-field precision rules (preventive)

> Preventive rules that apply to every DApp doing EIP-712 signing — must be followed when writing scaffold conversion code.

### The problem

EIP-712 `uint64`-and-larger integer fields, if sent as JavaScript `Number`, hit `Number.MAX_SAFE_INTEGER = 2^53 − 1` and **silently lose precision**. The signature hash mismatches what the chain validates, and the failure is hard to reproduce (it shows up as on-chain validation failure, not a frontend error).

| Type | Safe range | Number safe? |
|------|------------|--------------|
| `uint8` / `uint16` / `uint32` | up to 4B | ✅ Safe |
| `uint64` | up to ~1.8×10¹⁹ | ❌ May lose precision |
| `uint128` / `uint256` | far exceeds Number.MAX_SAFE_INTEGER | ❌ Must use BigInt |
| `int*` | same rules | same |

### Correct pattern

```typescript
// ❌ Wrong — may silently lose precision
const typedData = {
  message: {
    sigDeadline: permitData.values.sigDeadline,   // JS Number
    amount:      quote.amount,                    // JS Number
  }
};

// ✅ Right — every uint*/int* field consistently goes through BigInt-string
function toSafeInt(v: unknown): string {
  if (v === null || v === undefined) throw new Error(`EIP-712 field is null`);
  return BigInt(String(v)).toString();
}

const typedData = {
  message: {
    sigDeadline: toSafeInt(permitData.values.sigDeadline),
    amount:      toSafeInt(quote.amount),
  }
};
```

### Equivalent in `jq`

When constructing `message` via `jq`, force every numeric field from the API to a string (jq's `tostring` preserves precision):

```bash
echo "$PERMIT_DATA" | jq '.values | .sigDeadline |= tostring | .nonce |= tostring'
```

### Scaffold auto-detection

When generating `index.ts`, for every assignment to an EIP-712 `message` field, the scaffold **must** check the type:

- If the API return type is `number` AND the EIP-712 type is `uint64` or larger → auto-wrap with `BigInt(...).toString()`
- If the type can't be determined → leave a `TODO [third-party]` comment asking the developer to confirm manually

---

## Appendix D — DApp-specific notes

**Uniswap**: standard monorepo layout; skills live under `packages/plugins/[plugin]/skills/[name]/`. Direct `cp` works. Form A upgrade path (since the source has `index.ts`). `businessType=swap` is the most common use case.

**GMX**: flat `skills/[name]/` layout; subdir is two levels shallower than Uniswap. `businessType=contract-call` triggers the Form B (markdown-only) stub generation path.

**Morpho**: same flat layout as GMX, but the repo is pre-v1.0 experimental — the schema may drift. For production tests, pin a commit SHA: after `git clone`, run `cd "$TMP_DIR"; git checkout <commit-sha>`. Both `skills/morpho-cli` and `skills/morpho-builder` exist; pick `morpho-cli` (the business skill) for testing — `morpho-builder` is a meta code-generation skill.

## Appendix E — Updating the scaffold

The scaffold repo is MIT-licensed and public. Future versions don't require re-downloading a zip — just `cd` into the skill directory and `git pull`:

```bash
cd ~/.agents/skills/onchainos-dapp-scaffold
git pull origin main

# Check the new version
grep "^version:" SKILL.md
```

> After repo migration, the upstream remote will need to be updated:
> ```bash
> git remote set-url origin https://github.com/okx/dapp-connect-agenticwallet
> git pull origin main
> ```

## Failure-report template

When you hit a problem, paste the following into the Lark thread / issue comment:

```
DAPP_CHOICE=<your choice>
Stuck at H2 section=
Full error message=
OS=macOS XX / Linux XX
Agent CLI version=$(claude --version || codex --version || openclaw --version)
Node version=$(node --version)
Git version=$(git --version)
Scaffold version=$(grep '^version:' ~/.agents/skills/onchainos-dapp-scaffold/SKILL.md)
```
