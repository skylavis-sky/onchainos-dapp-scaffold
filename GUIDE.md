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

## Appendix F — Troubleshooting

Use Ctrl-F on the symptom you're seeing. Entries are grouped by phase.

---

### F1 · Install & scaffold setup

**`SKILL.md missing` or `templates/ missing` after install**
Re-run the install or pull the latest:
```bash
rm -rf ~/.agents/skills/onchainos-dapp-scaffold
curl -fsSL https://raw.githubusercontent.com/okx/dapp-connect-agenticwallet/main/install.sh | sh
```

**Scaffold installed but agent doesn't recognize it**
The agent's skill registry is cached at startup. Restart your agent (close + reopen Claude Code / Codex / Cursor) after install.

**Symlink fails on Windows / WSL**
`ln -s` may require Developer Mode on Windows. Use a direct copy instead:
```bash
cp -r ~/.agents/skills/onchainos-dapp-scaffold ~/.claude/skills/onchainos-dapp-scaffold
```

---

### F2 · Source preparation — violation scan

**Upgrade blocked: `ethers.Wallet` / `signTransaction` / `sendTransaction` / `privateKey` detected**
The source contains local signing code. Remove all signing, key-loading, and broadcast calls. Keep only calldata construction. Clean the source, then re-run the scaffold.

**Upgrade blocked: `walletClient.sendTransaction` or `useWriteContract` detected (wagmi/viem)**
Replace with the `pending_sign` pattern: build `unsigned_tx` from the API response and return it. Remove the wagmi/viem signing hooks.

**Upgrade blocked: `forge script --broadcast` or `cast send` detected**
Extract the contract ABI and calldata. Return a `pending_sign` wrapping that calldata. Drop the Foundry broadcast call.

**False positive: violation keyword in a test file, comment, or type import**
Exclude non-production directories before scanning. Annotate unavoidable false positives with `// onchainos-scan-ignore` on that line. Re-run.

**False positive: `privateKey` is an API response field or URL parameter, not a signing key**
Rename the field to something non-flagging (e.g. `apiToken`, `authKey`). If renaming breaks an upstream contract, add `// onchainos-scan-ignore` on the specific line.

**Violation detected in `references/` subdirectory, not in main skill files**
The scanner covers only the root skill files by default. Violations in `references/` are advisory — clean them if they'll be executed, ignore them if they're documentation only.

---

### F3 · Form detection edge cases

**`index.ts` exists but is empty or contains only comments → misdetected as Form A**
The detection command `grep -q '^export' index.ts` will correctly return Form B when there are no export statements. If it returns Form A, verify the file has no `export` lines at the start of any line.

**`export async function` not matched by form-detection grep**
The relaxed pattern `grep -qE '^export' index.ts` covers `export async function`, `export const`, `export default`. If detection still fails, open `index.ts` and confirm your function declarations begin with `export` at column 0.

**Source has `index.ts` with syntax errors → parser fails before form detection**
Fix TypeScript syntax first: `node --check index.ts` or `tsc --noEmit`. Re-run once clean.

---

### F4 · Upgrade: Form A specific

**Tool classified as read-only because its name starts with `get`, but it returns transaction calldata**
Classification is based on the return type, not the function name. If the function returns `{to, data, value, chain}`, it is always a Transaction tool regardless of name. Confirm with the agent.

**`import` statements break after functions are renamed to `_impl` suffix**
The scaffold is designed for single-file skills. If your source imports functions across files, consolidate to a single `index.ts` before running the upgrade.

**`toSafeInt()` helper was injected but `uint*/int*` fields in `sign-message` payload are still plain numbers**
Check the generated `sign-message` function's `return.message` block. Every numeric field that maps to a Solidity `uint*` or `int*` type must be wrapped: `amount: toSafeInt(apiResp.amount)`. See Appendix C.

**Generated `index.ts` has no `export` statement at the end**
Self-check A5 will catch this. Add manually: `export { toolName1, toolName2 };` as the final line, then re-run the self-checks.

**`TODO [third-party]` placeholders are still in the generated file**
These are intentional fail-fast markers. After generation, search for `TODO [third-party]` and fill in every business logic block (API base URL, route call, calldata encoding). The scaffold will not fill these in for you.

---

### F5 · Upgrade: Form B specific

**Scanner finds no signing keywords — no line mapping is produced**
This is not an error. The source uses an API-relay pattern: the API already returns `{to, data, value}`. The routing conversion section should use the adapter-wrap template, which maps each API response field directly into `unsigned_tx` without needing to replace a local signing call.

**Read-only tool (`get_position`, `query_balance`) appears in the routing conversion section**
Read-only tools must not be mapped. Any tool whose sole purpose is to call a GET endpoint and return data should be listed in the routing section as: `get_position — read-only, no replacement needed`.

**LLM batches approval + supply into a single `pending_sign` return**
Multi-step flows require two separate sequential returns. The routing conversion section must state this explicitly:
1. Return approval `pending_sign` → wait for `txHash`
2. Return supply `pending_sign` → wait for `txHash`
Never batch both into one object.

**Original `requiredTools` in source gets overwritten instead of merged**
The correct behaviour is a union. If the output `requiredTools` is missing entries from the source, add them back manually and re-run the self-check.

**Output skill is named `my-skill-onchainos-onchainos`**
The scaffold should strip any existing `-onchainos` suffix before appending the new one. Fix the `name` field in the generated frontmatter manually.

---

### F6 · Self-check failures

**A1: `{{VARIABLE}}` still visible in output**
A template variable was not substituted. Search all output files for `{{` and identify which variable is unresolved. Re-run the scaffold step that populates that variable.

**A2: YAML frontmatter is invalid**
Test the frontmatter block directly:
```bash
python3 -c "import yaml; yaml.safe_load(open('<output>/SKILL.md'))"
```
Common causes: unquoted colon in a description line, mismatched pipe (`|`) block, bad indentation in `requiredTools`.

**A3: `## Pre-flight Checks` section is missing from output**
Four markers are required in every generated skill: `[onchainOS dependency]`, `[signing constraint]`, `## Pre-flight Checks`, `## Signing Constraint`. If any are absent, the scaffold did not complete Step 3. Re-run.

**A4/A5: reported as FAIL instead of SKIP for a Form B output**
A4 and A5 only apply to Form A (they check `index.ts`). A Form B output has no `index.ts` and must report SKIP for both. If they show FAIL, the self-check logic is running A4/A5 on the markdown files. Disregard if the output has no `index.ts`.

---

### F7 · Runtime: initialization

**`onchainos --version` returns "command not found" immediately after install**
The install script writes to `~/.local/bin`. The current shell session doesn't know about it yet. Run:
```bash
export PATH="$HOME/.local/bin:$PATH"
onchainos --version
```
The generated skill's Initialization block does this automatically — do not bypass it.

**`onchainos --version` succeeds but the skill reports missing subcommands**
An older version of onchainos is installed. The binary-exists check passes but the required subcommands aren't present. Re-install:
```bash
curl -fsSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh
```

**Initialization block skipped on re-invocation**
The Initialization block must run on **every** invocation, not just the first. It is idempotent — safe to repeat. If your agent skips it, check that the SKILL.md description block still contains the `BEFORE ANY RESPONSE` instruction.

---

### F8 · Runtime: `pending_sign` format errors

**`onchainos wallet contract-call` returns "invalid chain format"**
`chain` must be CAIP-2: `eip155:1` (Ethereum), `eip155:137` (Polygon), `eip155:42161` (Arbitrum). Strings like `ethereum`, `mainnet`, or `1` are not accepted.

**`onchainos wallet contract-call` returns "invalid address"**
`to` must be a checksummed or lowercase hex address. Validate before returning:
```ts
to: rawAddress.toLowerCase()   // or ethers.getAddress(rawAddress)
```

**`onchainos wallet contract-call` returns "invalid data"**
`data` must be a `0x`-prefixed hex string. Prefix if missing:
```ts
data: data.startsWith('0x') ? data : '0x' + data
```

**`onchainos wallet contract-call` returns "invalid value"**
`value` must be a hex string for EVM: `'0x0'` for no-value calls, or `'0x' + BigInt(weiAmount).toString(16)`.

**Agent returns `pending_sign` but does not route to onchainOS**
Verify two things: (1) the `requiredTools` block in SKILL.md lists the tool by its exact name (e.g. `onchainos wallet contract-call` — spaces, not hyphens); (2) `next_action.tool` in the returned JSON matches that name exactly.

---

### F9 · Runtime: EIP-712 / sign-message

**`onchainos wallet sign-message` returns "missing msgHash" or signature fails on-chain**
The API likely returns a non-standard EIP-712 shape. The required shape is:
```json
{ "types": {...}, "primaryType": "...", "domain": {...}, "message": {...} }
```
If the API returns `values` instead of `message`, or omits `primaryType`, convert before returning. See Appendix B for a Uniswap walkthrough.

**Signature is accepted by onchainOS but on-chain verification fails silently**
A numeric field (`uint64`, `uint128`, `uint256`) is being passed as a JavaScript `Number`, causing precision loss above 2^53−1. Wrap every such field with `toSafeInt()`:
```ts
deadline: toSafeInt(apiResponse.deadline)
```
See Appendix C for the full rule set.

**`pending_sign` for a sign-message tool uses `unsigned_tx` instead of `message`**
`sign-message` tools must return `message: <eip712-or-personal-sign-payload>`, not `unsigned_tx`. The two shapes are not interchangeable.

---

### F10 · Runtime: multi-step flows & session

**Second transaction executes before the first is confirmed**
Multi-step flows (e.g. ERC-20 approval → supply) must be sequential. After routing the first `pending_sign` to onchainOS and receiving `txHash`, confirm on-chain before proceeding:
```bash
onchainos wallet status <txHash>
```
Do not batch both steps into a single `pending_sign`.

**User says "on Arbitrum" but the skill hardcodes `chain: 'eip155:1'`**
Accept `chain` as a parameter and pass it through:
```ts
async function myTool(params: { chain?: string }) {
  const chain = params.chain ?? 'eip155:1';
  return { ..., unsigned_tx: { ..., chain } };
}
```

**`onchainos wallet status` returns `loggedIn: false` mid-session**
Session has expired. Re-authenticate:
```bash
onchainos wallet login user@example.com
onchainos wallet verify <6-digit-code>
```

**Transaction reverts on-chain despite valid `pending_sign` format**
Swap/quote calldata expires (typically 30 s–5 min). Do not cache a `pending_sign` object across invocations. Rebuild the route and calldata on every tool call.

---

## Failure-report template

When you hit a problem, paste the following into the Lark thread / issue comment:

```
DAPP_CHOICE=<your choice>
Stuck at section=
Full error message=
OS=macOS XX / Linux XX
Agent CLI version=$(claude --version || codex --version || openclaw --version)
Node version=$(node --version)
Git version=$(git --version)
Scaffold version=$(grep '^version:' ~/.agents/skills/onchainos-dapp-scaffold/SKILL.md)
```
