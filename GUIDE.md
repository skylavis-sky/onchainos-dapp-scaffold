# DApp Skill Integration Guide

> For **maintainers** validating the scaffold against known test endpoints, see [TESTING.md](TESTING.md).

This guide walks a DApp developer through upgrading an existing DApp skill to route signing and broadcasting through Onchain OS. The scaffold converts your skill — it does not generate one from scratch.

## Which path do you need?

| Situation | Where to go |
|-----------|-------------|
| You have an existing DApp skill and want to add Onchain OS signing | **This guide** — Parts 1–3 |
| You want to write `pending_sign` wrappers by hand without the scaffold | See [SKILL.md](SKILL.md) for the `pending_sign` contract and routing rules, then [Part 3](#part-3--test-your-upgraded-skill) to test and [Appendix F](#appendix-f--troubleshooting) for runtime errors |
| Something went wrong after running the scaffold | [Appendix F — Troubleshooting](#appendix-f--troubleshooting) |

## Prerequisites

- An existing DApp skill (your own, or a fork of a third-party DApp's published skill)
- The scaffold installed at `~/.agents/skills/onchainos-dapp-scaffold/` (see [README.md](README.md#quick-start))
- An AI agent (Claude Code, OpenClaw, Codex, Cursor, etc.) that reads from `~/.agents/skills/`
- The Onchain OS CLI — the scaffold installs it automatically on first use

## Part 1 — Run the upgrade

Install the scaffold if you haven't already:

```bash
curl -fsSL https://raw.githubusercontent.com/okx/dapp-connect-agenticwallet/main/install.sh | sh
```

Then restart your AI agent so it picks up the new skill.

Place your DApp skill somewhere under `~/.agents/skills/` (or `~/.claude/skills/` for Claude Code), then ask your agent:

```
Use the scaffold to upgrade the DApp Skill at ~/.agents/skills/<your-skill>
```

To override the detected `businessType` (e.g. the scaffold misidentifies a contract-call skill as a swap):

```
Use the scaffold to upgrade the DApp Skill at ~/.agents/skills/<your-skill>, businessType=contract-call
```

The scaffold detects whether your source is [Form A or Form B](README.md#quick-start) automatically.

**What the scaffold does:**

1. Scans for local signing code (`ethers.Wallet`, `sendTransaction`, `privateKey`, etc.) — blocks the upgrade if found
2. Detects the source form and `businessType`
3. Generates a new skill at `<your-skill>-onchainos/` adjacent to the input
4. Installs the Onchain OS CLI if not present
5. Runs self-checks (A1–A5) to verify the output

The original skill is untouched. You can roll back at any time by removing the `-onchainos` directory.

> After the upgrade completes, restart your agent again so it picks up the new `<your-skill>-onchainos` skill — see Part 3.

## Part 2 — Verify the output

After the upgrade, run these commands to confirm the output is well-formed:

```bash
SKILL_DIR=~/.agents/skills/<your-skill>-onchainos

# Output directory was created
ls "$SKILL_DIR/SKILL.md"

# Four required markers are present
grep -c '\[Onchain OS dependency\]' "$SKILL_DIR/SKILL.md"  # Expected: 1
grep -c '\[signing constraint\]'   "$SKILL_DIR/SKILL.md"  # Expected: 1
grep -c '## Pre-flight Checks'     "$SKILL_DIR/SKILL.md"  # Expected: 1
grep -c '## Signing Constraint'    "$SKILL_DIR/SKILL.md"  # Expected: 1

# Template variables were all substituted
grep -c "{{" "$SKILL_DIR/SKILL.md"  # Expected: 0

# Frontmatter name ends with -onchainos
grep "^name:" "$SKILL_DIR/SKILL.md"
```

For Form A upgrades (source had `index.ts`), also check:

```bash
# index.ts exists and has no unresolved TODOs
ls "$SKILL_DIR/index.ts"
grep -c "TODO \[third-party\]" "$SKILL_DIR/index.ts"  # 0 if you've filled them in; >0 if pending
```

If any check fails, see [Appendix F — Troubleshooting](#appendix-f--troubleshooting).

## Part 3 — Test your upgraded skill

Restart your agent after upgrading so the new skill is picked up.

### Auth check

```
Use <your-skill>-onchainos to check if Onchain OS is ready
```

Expected: the skill runs its Initialization block, confirms `onchainos --version`, then reports ready.

### Read-only call

Run a read-only tool first (positions, balances, quotes) to confirm the skill can reach your DApp's API without triggering signing:

```
Use <your-skill>-onchainos to [read-only action, e.g. "get my position on Ethereum"]
```

Expected: data returned directly; no `pending_sign` object; no Onchain OS call.

### Transaction (preview)

Run a transaction-producing tool without a wallet address or with a dry-run flag to see the `pending_sign` shape before committing:

```
Use <your-skill>-onchainos to [action] — quote only, no broadcast
```

Expected: skill returns a `pending_sign` object with `unsigned_tx.chain` in CAIP-2 format (e.g. `eip155:1`), `unsigned_tx.data` starting with `0x`, and `next_action.tool` set to `onchainos wallet contract-call` (or `send` / `sign-message` as appropriate).

### Live transaction

Once preview looks correct, run a small live transaction:

```
Use <your-skill>-onchainos to [minimal real action, e.g. "swap 0.001 USDC for ETH on Base"]
```

Expected flow:
1. Skill builds calldata, returns `pending_sign`
2. Agent passes it to `onchainos wallet contract-call`
3. Onchain OS signs inside TEE and broadcasts
4. Agent receives `txHash` and reports confirmation

### Multi-step flow (if applicable)

For skills with approval + action sequences:

```
Use <your-skill>-onchainos to [action requiring token approval first]
```

Expected: two sequential `pending_sign` returns — first the approval, then the action. The agent must not batch both into a single object.

---

## Appendix A — Why some skills don't go through this flow

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

**GMX**: flat `skills/[name]/` layout; subdir is two levels shallower than Uniswap. `businessType=contract-call` triggers the Form B (markdown-only) conversion path.

**Morpho**: same flat layout as GMX, but the repo is pre-v1.0 experimental — the schema may drift. For production integrations, pin a commit SHA: after `git clone`, run `cd "$TMP_DIR"; git checkout <commit-sha>`. Both `skills/morpho-cli` and `skills/morpho-builder` exist; pick `morpho-cli` (the business skill) — `morpho-builder` is a meta code-generation skill.

## Appendix E — Updating the scaffold

The scaffold repo is MIT-licensed and public. Future versions don't require re-downloading — just `cd` into the skill directory and `git pull`:

```bash
cd ~/.agents/skills/onchainos-dapp-scaffold
git pull origin main

# Check the new version
grep "^version:" SKILL.md
```

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
Four markers are required in every generated skill: `[Onchain OS dependency]`, `[signing constraint]`, `## Pre-flight Checks`, `## Signing Constraint`. If any are absent, the scaffold did not complete Step 3. Re-run.

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

**Agent returns `pending_sign` but does not route to Onchain OS**
Verify two things: (1) the `requiredTools` block in SKILL.md lists the tool by its exact name (e.g. `onchainos wallet contract-call` — spaces, not hyphens); (2) `next_action.tool` in the returned JSON matches that name exactly.

---

### F9 · Runtime: EIP-712 / sign-message

**`onchainos wallet sign-message` returns "missing msgHash" or signature fails on-chain**
The API likely returns a non-standard EIP-712 shape. The required shape is:
```json
{ "types": {...}, "primaryType": "...", "domain": {...}, "message": {...} }
```
If the API returns `values` instead of `message`, or omits `primaryType`, convert before returning. See Appendix B for a Uniswap walkthrough.

**Signature is accepted by Onchain OS but on-chain verification fails silently**
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
Multi-step flows (e.g. ERC-20 approval → supply) must be sequential. After routing the first `pending_sign` to Onchain OS and receiving `txHash`, confirm on-chain before proceeding:
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

When you hit a problem, paste the following into the issue comment or support thread:

```
Skill name=<your-skill>
Stuck at section=
Full error message=
OS=macOS XX / Linux XX
Agent CLI version=$(claude --version || codex --version || openclaw --version)
Node version=$(node --version)
Git version=$(git --version)
Scaffold version=$(grep '^version:' ~/.agents/skills/onchainos-dapp-scaffold/SKILL.md)
```
