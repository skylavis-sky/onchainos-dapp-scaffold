---
name: onchainos-dapp-scaffold
version: "1.4.0"
author: "okx"
description: |
  Upgrade an existing DApp Skill into one compatible with the OnchainOS routing
  contract. The scaffold reads the source skill, classifies its tools, wraps
  transaction/signing tools in a pending_sign shell, injects required spec
  sections, and runs self-checks.

  This scaffold does **not** generate skills from scratch. Bring an existing
  DApp skill — the scaffold's job is to convert, not to invent.

  [Trigger phrases]
  Use the scaffold to upgrade <skill-dir>
  Upgrade DApp Skill at <skill-dir>
  用脚手架升级 <skill-dir>
  升级 DApp Skill：路径 <skill-dir>

  Examples:
    "Use the scaffold to upgrade ~/.claude/skills/my-dex"
    "用脚手架升级 ~/.claude/skills/uniswap-ai-test"

  The scaffold reads the directory (Form A = has index.ts; Form B = markdown
  only) and injects pending_sign wrappers + next_action.tool routing +
  requiredTools + the 3 fixed spec sections per the OnchainOS schema.

  [Scope] Claude Code (and forks that fully implement the Skill loading
  protocol, e.g. OpenClaw). Cursor / Codex CLI / OpenCode lack a Skill loader
  and need an MCP-based integration (separate scaffold).

triggers:
  - "用脚手架升级"
  - "升级 DApp Skill"
  - "Use the scaffold to upgrade"
  - "Upgrade DApp Skill"
  - "upgrade onchainOS DApp"
---

# OnchainOS DApp Integration Scaffold

> **🚧 Migration notice**: This scaffold's repo is moving from
> `skylavis-sky/onchainos-dapp-scaffold` to `okx/dapp-connect-agenticwallet`.
> Both URLs will work during transition; bookmark the new one.

This Skill is an AI workflow definition. The agent reads this file and
executes the upgrade workflow described below.

## Scope & runtime model (must tell the user before generating)

**Output works in:** Claude Code (and Skill-protocol-compatible forks like
OpenClaw, when fully compatible).
**Does NOT work in:** Cursor / Codex CLI / OpenCode — they lack a Skill
loader and need the separate MCP-based scaffold.

**Runtime model:** `index.ts` is never executed by any process. A Claude Code
Skill is a Markdown instruction. The actual execution path is:
LLM reads `index.ts` → simulates the function body during reasoning (calling
Bash/WebFetch tools to fetch real data) → returns JSON conforming to the
`pending_sign` contract → Claude routes per `next_action.tool` to OnchainOS.

**Therefore this approach fits:** pure-function tools that build calldata
(swap route lookup + encode, transfer address validation, etc.).
**Does NOT fit:** multi-step retry, WebSocket subscriptions, complex state
machines, heavy business logic — use the MCP scaffold instead.

---

## Workflow: upgrade an existing DApp Skill

When the user provides any of these inputs (any combination is recognized as
the upgrade flow):

1. The scaffold spec doc (this SKILL.md, or the OnchainOS DApp integration
   guide § 3 "Skill integration")
2. The scaffold itself (`onchainos-dapp-scaffold` — this skill)
3. The third-party DApp's existing Skill (path like `~/.claude/skills/<dapp-name>/`)

**Example trigger phrase:**
```
I have an existing DApp Skill at ~/.claude/skills/my-dex.
Upgrade it per the OnchainOS Skill spec, output to ~/.claude/skills/my-dex-onchainos/
```

### Workflow (7 steps, includes a form fork)

#### Step 1 — Read the source DApp Skill

- `<src>/SKILL.md` → parse frontmatter (name / version / author / tools array)
  + description + full body
- `<src>/index.ts` → if present, identify each function signature, return
  type, and any existing signing logic
- `<src>/README.md` (if present) → extract DApp business description
- `<src>/references/` or other subdirectories → record paths; may need full
  copy later

#### Step 1.5 — Form detection (critical fork)

The form determines the rest of the flow. **Do not skip this step.**

| Detection | Form | Path |
|-----------|------|------|
| `<src>/index.ts` exists AND has exported business functions | **Form A** | Steps 2a → 3a → 4a → 5 → 6 (original code-bearing flow) |
| Only `<src>/SKILL.md`, no index.ts, OR index.ts has no exports | **Form B** | Steps 2b → 3b → 4b → 5 → 6 (markdown-merge flow) |
| Local-signing code already detected (see § Hard constraints item 3 for full keyword list) | **Violation** | **Stop immediately**, ask the user to clean the source first, then retry |

**Form-detection command:**
```bash
test -f <src>/index.ts && grep -q '^export' <src>/index.ts && echo "Form A" || echo "Form B"
```

**Violation-scan command** (must run BEFORE form detection):
```bash
grep -rn \
  'ethers\.Wallet\|new Wallet(\|signTransaction\|sendTransaction\|privateKey\|Keypair\.fromSecret\|nacl\.sign\|forge script.*--broadcast\|cast send\|useSignMessage\|useWriteContract\|signUserOp\|HDNodeWallet\|mnemonicToAccount\|window\.ethereum\.request.*eth_send\|walletClient\.writeContract\|walletClient\.sendTransaction' \
  <src>/ 2>/dev/null | grep -v '^.*:.*\/\/' | head -20
# Any output = report violation, stop immediately.
```

---

### Form A path (source has executable code)

#### Step 2a — Classify each tool (decides whether to wrap in pending_sign)

Classify per tool:

| Detection | Class | Action |
|-----------|-------|--------|
| Function name contains `build` / `swap` / `mint` / `deposit` etc. + returns tx/calldata | Transaction | Wrap with pending_sign |
| Function name contains `send` / `transfer` + has to+amount params | Transfer | Wrap with pending_sign → `onchainos wallet send` |
| Function name contains `sign` / `login` / `authorize` + returns message | Signing | Wrap with pending_sign → `onchainos wallet sign-message` |
| Function name contains `get` / `query` / `search` / `list` + returns plain JSON | Read-only | **Untouched**, pass through |
| Already contains `ethers.Wallet` / `signTransaction` / `privateKey` | **Violation** — source signs locally | Tell user: must remove local signing first before integrating OnchainOS |

#### Step 3a — Synthesize new SKILL.md (merge strategy, v1.4)

Use a **merge** strategy, not a rewrite — every original frontmatter field
must be preserved; only inject the scaffold's required fields:

1. **Read all original frontmatter fields** (including `allowed-tools`,
   `model`, `license`, `metadata`, and any non-standard fields)
2. **Override these fields** (scaffold values win):
   - `name` = original name + `-onchainos` suffix (don't double-append if
     already suffixed)
   - `version` = original patch +1 (e.g. `1.2.0` → `1.2.1`)
   - `description` = inject `[onchainOS dependency]` + `[signing constraint]`
     blocks (append to original description, don't replace)
   - `requiredTools` = union of OnchainOS tools matched by the transaction /
     transfer / signing tools (union with existing `requiredTools` if any)
3. **Preserve every other original field** (`author`, `chains`, `tools`,
   `allowed-tools`, `model`, `license`, `metadata`, etc.) — must not silently
   drop
4. **Post-merge check**: new SKILL.md frontmatter field count ≥ original;
   if it decreases, list the dropped fields and warn the user
5. Inject `## Pre-flight Checks` + `## Signing Constraint` sections (copied
   verbatim from `templates/SKILL.md.template`)
6. **Original SKILL.md body** (markdown after the frontmatter) is **kept in
   full**, appended after the new frontmatter as the business description

#### Step 4a — Synthesize new index.ts

- Inject the `RUNTIME MODEL` warning at the top (copied from
  `templates/index.ts.template`)
- **Also inject the `toSafeInt` helper at the top** (copied from
  `templates/index.ts.template`) — inject unconditionally regardless of
  whether sign-message tools are present, to avoid omission
- **Original business functions** → rename with `_impl` suffix (e.g.
  `my_build_swap` → `_my_build_swap_impl`), kept as internal helpers
- **Each transaction tool** → generate a new outer function, wrap in
  `pending_sign` skeleton, internally call the `_impl` to get `unsigned_tx`
- **Signing tools** (sign-message) → during wrapping, additionally:
  - Replace every EIP-712 `uint*/int*` field in the `_impl` return's `message`
    with `toSafeInt(...)` calls
  - If the original `_impl` returns non-standard `{domain, types, values}`,
    inject the standard-format conversion in the outer function (see
    Appendix B / sign-message skeleton comments)
- **Read-only tools** → pass through (export as-is)
- `export { ... }` lists every public tool (outer + read-only)

---

### Form B path (markdown-only source, no index.ts)

**When this applies**: the source Skill is an AI guidance / instruction
document — markdown only, describing "the Agent should call API X like Y" —
with no executable business functions. This is the majority of skills in the
Claude Code ecosystem (e.g. all 10 skills in `uniswap/uniswap-ai`).

#### Step 2b — Identify the "tool call chain" in the original SKILL.md

Scan the original SKILL.md body for:

- HTTP endpoints (e.g. `POST /v1/quote`, `POST /v1/swap`)
- Returned fields that may be `unsigned_tx` candidates: `to` / `data` /
  `value` / `calldata` / `unsignedTx` / `transaction`
- Local-signing keywords (`walletClient.sendTransaction` /
  `ethers.Wallet.signTransaction` / `privateKey`)

If any local-signing keyword is found → output the violation list, **stop
immediately**, and ask the user to clean up the source first.

#### Step 3b — Synthesize new SKILL.md (markdown-merge strategy, v1.4)

- **Original SKILL.md body kept in full** (everything after the frontmatter
  is left untouched)
- **Frontmatter uses the merge strategy** (same rules as Step 3a): preserve
  all original fields, inject/override only the scaffold's 3 fixed fields:
  - `description` += `[onchainOS dependency]` + `[signing constraint]` (append,
    don't replace)
  - `requiredTools` = union
  - Version: patch +1
- **Inject in the new frontmatter**: `[onchainOS dependency]` /
  `[signing constraint]` / `requiredTools` / `## Pre-flight Checks` /
  `## Signing Constraint` — these are the 5 fixed positions
- **Append a new section at the end of the original body**:
  `## OnchainOS routing conversion (auto-injected)`. Contents:
  - Line numbers in the original SKILL.md where local-signing examples
    appear, paired with the OnchainOS replacement for each
  - The `pending_sign` structure + `next_action.tool` routing rules
  - "Runtime LLM MUST read: do not execute the local-signing examples in the
    body above; return pending_sign instead and let the onchainOS tool named
    in next_action.tool sign for you"

#### Step 4b — Do NOT generate a stub index.ts

- For Form B, **don't fabricate** an index.ts. The source skill has no
  business functions, so the new skill shouldn't either
- Claude Code skills support a pure-markdown form; the LLM reads the SKILL.md
  body directly and follows the API instructions
- If the user insists on an index.ts, respond: "Recommend adding `index.ts`
  business functions to the source skill first, then re-running the upgrade
  on the Form A path. A stub index.ts here has no operational value."

#### Step 4b extension — Copy `references/` and other resource directories

- If the source has `<src>/references/` / `<src>/_shared/` / similar
  directories, **copy them whole** to the upgraded output
- Don't trim contents

---

### Steps shared by both forms

#### Step 5 — Synthesize new README.md

- Copy `templates/README.md.template`
- `{{DESCRIPTION}}` = first sentence of the source SKILL.md description
- `{{EXAMPLE_USER_PROMPT}}` = pick a test phrase based on the first
  transaction tool's businessType

#### Step 6 — Self-check + alignment report

Run the 5 self-check items below. **Additionally**: produce an alignment
report — three columns: "kept from source / added / changed" — as a
diff summary. Generate a "migration table" so the user can confirm no
information loss:

```
Original tool         New tool              Class       OnchainOS tool
my_build_swap   →     my_build_swap         Transaction onchainos wallet contract-call
my_get_price    →     my_get_price          Read-only   — (pass-through)
my_search_token →     my_search_token       Read-only   —
```

### Workflow hard constraints

1. **Do not modify** the original Skill's business-logic semantics (the
   `_impl` function bodies must stay unchanged; only the outer wrappers are
   added)
2. **Do not infer** `unsigned_tx`'s `to` / `data` — those must be returned by
   the original `_impl` function. The workflow only wraps them into a
   `pending_sign` outer shell.
3. If the source already contains local-signing code (ethers.Wallet etc.),
   **abort at Step 2** and ask the user to clean the source first.

---

## Self-check (mandatory after every upgrade, do not skip)

Run mechanical checks against the upgrade output. Run each Bash command and
report the consolidated result to the user:

```bash
D=<outputDir>
# A1: no unresolved variables
grep -l '{{' $D/* && echo FAIL:A1 || echo PASS:A1
# A2: YAML frontmatter is valid
python3 -c "import yaml,sys; yaml.safe_load(open('$D/SKILL.md').read().split('---',2)[1])" && echo PASS:A2 || echo FAIL:A2
# A3: 3 fixed sections present
grep -q '\[onchainOS dependency\]' $D/SKILL.md && grep -q '\[signing constraint\]' $D/SKILL.md && grep -q '## Pre-flight Checks' $D/SKILL.md && grep -q '## Signing Constraint' $D/SKILL.md && echo PASS:A3 || echo FAIL:A3
# A4: no local signing residue (expanded pattern set — covers JS, Solana, Foundry CLI, wagmi, ERC-4337, HD, API-relay)
grep -v '^//' $D/index.ts 2>/dev/null | grep -qE \
  'ethers\.Wallet|new Wallet\(|signTransaction|sendTransaction|privateKey|mnemonic|keystore|\
Keypair\.fromSecret|nacl\.sign|forge\s+script.*--broadcast|cast\s+send|anchor\s+deploy|\
useSignMessage|useWriteContract|useWalletClient|writeContract\(\
|signUserOp|UserOperation|signTypedData\(|eth_sendTransaction|eth_sendRawTransaction|\
HDNodeWallet|mnemonicToAccount|deriveChild|\
window\.ethereum\.request.*eth_send|window\.ethereum\.send\b' \
  && echo FAIL:A4 || echo PASS:A4
# A5: pending_sign contract present
grep -q 'pending_sign' $D/index.ts 2>/dev/null && grep -q 'next_action' $D/index.ts 2>/dev/null && echo PASS:A5 || echo FAIL:A5
```

**Expected:** all 5 PASS for Form A. Form B: A1/A2/A3 PASS, A4/A5 SKIP (no `index.ts`).
Any FAIL → tell the user which item failed and propose a fix; **do not** claim
the upgrade succeeded.

---

## pending_sign skeletons (used by Step 4a's wrappers)

For each transaction-class tool wrapped in Form A's Step 4a, use one of these
skeletons by businessType. Outside the `// TODO [third-party]` markers, copy
the skeleton verbatim:

```ts
// ───── swap / contract-call skeleton ─────
async function <NAME>(params: any): Promise<PendingSign> {
  // TODO [third-party] route lookup / pricing / build calldata
  const TODO = (field: string): never => {
    throw new Error(`[SCAFFOLD-UNFILLED] ${field} unfilled — fill in business logic or have the LLM substitute at runtime per the comment`);
  };
  const unsigned_tx = {
    to:    TODO('to'),       // target contract address
    data:  TODO('data'),     // ABI-encoded calldata
    value: '0',
    chain: '<PRIMARY_CHAIN>',
  };
  return {
    status: 'pending_sign',
    unsigned_tx,
    description: TODO('description'),   // human-readable summary
    next_action: { tool: '<NEXT_ACTION_TOOL>' },
  };
}

// ───── transfer skeleton ─────
async function <NAME>(params: any): Promise<PendingSign> {
  // TODO [third-party] parse to / amount / token
  const TODO = (f: string): never => { throw new Error(`[SCAFFOLD-UNFILLED] ${f}`); };
  const unsigned_tx = {
    to:    TODO('to'),       // recipient address
    data:  '0x',             // empty for native transfer; ERC-20 transfer needs encoded calldata
    value: TODO('value'),    // native amount (wei); for ERC-20 use '0'
    chain: '<PRIMARY_CHAIN>',
  };
  return {
    status: 'pending_sign',
    unsigned_tx,
    description: TODO('description'),
    next_action: { tool: '<NEXT_ACTION_TOOL>' },
  };
}

// ───── sign-message skeleton (off-chain, slightly different shape) ─────
async function <NAME>(params: any) {
  const TODO = (f: string): never => { throw new Error(`[SCAFFOLD-UNFILLED] ${f}`); };

  // ── EIP-712 precision rule (must read) ──────────────────────────────────────
  // Every uint*/int* field MUST be passed through BigInt(x).toString().
  // Never use JS Number — Number.MAX_SAFE_INTEGER = 2^53-1, so uint64+ silently
  // loses precision and the on-chain signature verification fails with no
  // frontend error (extremely hard to debug).
  //
  //   ❌ message: { sigDeadline: apiResponse.sigDeadline }          // Number, may lose precision
  //   ✅ message: { sigDeadline: BigInt(apiResponse.sigDeadline).toString() }
  // ─────────────────────────────────────────────────────────────────────────────

  // ── EIP-712 structure conversion (when API returns non-standard shape) ──────
  // If the third-party API returns { domain, types, values } instead of the
  // standard { types, primaryType, domain, message }, you MUST convert (or
  // onchainos errors with "missing msgHash"):
  //
  //   const typedData = {
  //     types:       { EIP712Domain: [...domainFields], ...apiResp.types },
  //     primaryType: Object.keys(apiResp.types).find(k => k !== 'EIP712Domain'),
  //     domain:      apiResp.domain,
  //     message:     apiResp.values,   // <── values → message
  //   };
  // ─────────────────────────────────────────────────────────────────────────────

  // TODO [third-party] build the message to sign, applying the rules above
  return {
    status: 'pending_sign',
    message: TODO('message'),               // personalSign string OR standard EIP-712 typed data
    description: TODO('description'),       // what this signature is for
    next_action: { tool: '<NEXT_ACTION_TOOL>' },
  };
}
```

**Why throw-style placeholders**:
- The legacy `'0xTODO'` string is a valid literal — the LLM in
  "simulate-execute" mode would return it as-is, then OnchainOS would get an
  invalid address and signing would fail
- `TODO('to')` throws immediately, forcing the LLM to either substitute a
  real value (per the comment, by calling the appropriate API) or ask the
  user for an API key — never fall through with a literal placeholder
- For DApp developers filling stubs by hand: `'0xTODO'` is easy to miss; a
  thrown error is impossible to ignore

**Composition rules**:
- Multiple tools: separate function bodies with one blank line
- End of file: append `export { <name1>, <name2>, ... };`
- `<PRIMARY_CHAIN>` = first element of the source's `chains` array
- `<NEXT_ACTION_TOOL>` = mapped from businessType per the table:

| businessType | next_action.tool | requiredTools |
|--------------|------------------|---------------|
| `swap` | `onchainos wallet contract-call` | `onchainos wallet contract-call`, `onchainos gateway broadcast` |
| `transfer` | `onchainos wallet send` | `onchainos wallet send`, `onchainos gateway broadcast` |
| `contract-call` | `onchainos wallet contract-call` | `onchainos wallet contract-call`, `onchainos gateway broadcast` |
| `sign-message` | `onchainos wallet sign-message` | `onchainos wallet sign-message` |
| `pipeline` | per-tool — see below | union of the above |

### `pipeline` businessType handling

`businessType = pipeline` means a Skill mixes **transaction tools + read-only
tools** (e.g. `search_token` / `get_price` / `build_swap` triple). When
wrapping:

1. For each tool, classify per Step 2a's table (transaction / transfer /
   sign-message / read-only)
2. Wrap transaction tools per their respective skeletons
3. **Read-only tools** use this skeleton (no pending_sign):

```ts
async function <NAME>(params: any) {
  // TODO [third-party] query (returns plain JSON, no signature)
  return { /* TODO [third-party] query result */ };
}
```

4. `requiredTools` = union (e.g. `[onchainos wallet contract-call, onchainos gateway broadcast]`); read-only tools **don't** contribute to requiredTools
5. `next_action.tool` is per-tool, **not shared**
6. When declaring read-only tools in SKILL.md `tools`, prefix description
   with `[read-only]` so the Agent can route correctly

---

## Hard constraints (must hold during every upgrade)

1. SKILL.md must contain the 3 fixed positions: `description`'s
   `[onchainOS dependency]` + `[signing constraint]` blocks, the
   `requiredTools` array, and the `## Pre-flight Checks` + `## Signing Constraint`
   sections
2. Every `index.ts` tool function's return value must conform to the
   `pending_sign` contract:
   `{ status, unsigned_tx: {to, data, value, chain}, description, next_action: {tool} }`
3. **Forbidden** (must never appear in upgrade output):

   **JS / TS inline signing**
   - `ethers.Wallet` / `new Wallet(...)` / `privateKey`
   - `signTransaction` / `sendTransaction`
   - `signTypedData(...)` / `eth_sendRawTransaction`
   - Direct `window.ethereum` write calls (`window.ethereum.request({method:'eth_send*'})` etc.)

   **Solana**
   - `Keypair.fromSecretKey(...)` / `nacl.sign(...)` / `nacl.sign.keyPair.fromSeed(...)`
   - `bs58.decode(<privateKey>)`

   **Foundry / Hardhat / Anchor CLI**
   - `forge script ... --broadcast` / `forge script ... --private-key`
   - `cast send` / `cast wallet sign`
   - `anchor deploy` / `anchor test --provider.wallet`

   **wagmi / viem hooks**
   - `useSignMessage` / `useWriteContract` / `useWalletClient`
   - `walletClient.writeContract(...)` / `walletClient.sendTransaction(...)`

   **ERC-4337 / Account Abstraction**
   - `signUserOp(...)` / direct `UserOperation` send

   **HD wallet derivation**
   - `HDNodeWallet` / `mnemonicToAccount` / `.deriveChild(...)`

   **Mnemonic / keystore / key file reads**
   - Reading `.env` private-key fields / decrypting keystore JSON / loading
     mnemonic strings

   **API-relayed unsigned tx**
   - External API returns `{to, data, value}` and code immediately calls
     `provider.sendTransaction(...)` or equivalent (must use the pending_sign
     adapter pattern instead)

4. If the user asks for "local signing" or "bypass OnchainOS" code, refuse
   immediately and steer them back to `pending_sign` + `next_action.tool`
   routing.

---

## v1.3 → v1.4 roadmap (known gaps · next-version fixes)

Based on real-world Mode-B-style upgrades against the 10 skills in
Uniswap/uniswap-ai, v1.2 surfaced these gaps. v1.3 fixed most; v1.4 ships
remaining fixes as part of the from-scratch removal.

### Gap 1 · Step 2b scanner only catches JS signing, misses CLI / API relay

The current Step 2b scanner covers JS inline signing (`sendTransaction` /
`walletClient.writeContract` / `ethers.Wallet`, etc.). **Missed cases:**

| Signing medium | Example pattern | Typical skill |
|----------------|-----------------|---------------|
| Foundry / Hardhat CLI | `forge script .* --broadcast` / `cast send .* --account` / `--private-key` | Any deployer-type skill (e.g. `uniswap-cca/deployer`) |
| Third-party wallet CLI | `tempo pay` / `tempo wallet send` / `rainbow send` | Any external wallet integration (e.g. `pay-with-any-token`) |
| Direct RPC | `eth_sendTransaction` / native JSON-RPC | Low-level EVM integrations |
| API-relayed unsigned tx | External API returns `{to, data, value}` + docs say "send / broadcast" | Aggregators like Uniswap Trading API, 1inch API |

**Fix:** expand the keyword set with 3 new scan patterns (CLI / RPC / API-relay);
any hit triggers the routing-conversion section.

### Gap 2 · Routing-conversion section had only one template

v1.2's "line-replacement" template (good for inline JS) didn't cover CLI or
API-relay scenarios.

**v1.4 ships three templates**:

**Pattern 1 · Line replacement** (existing) — for JS inline signing:
```
- L123: `walletClient.sendTransaction(...)` → pending_sign + onchainos wallet contract-call
- L456: `signTypedData(...)` → pending_sign + onchainos wallet sign-message
```

**Pattern 2 · Flow replacement** (new) — for CLI-driven signing:
```
Original flow: forge script ... --broadcast
Converted:
  1. forge build only (drop --broadcast)
  2. Extract constructor calldata from the artifact
  3. Wrap in pending_sign:
     { status, unsigned_tx: {to, data, value, chain}, next_action: {tool: 'onchainos wallet contract-call'} }
  4. OnchainOS takes over signing + broadcasting
```

**Pattern 3 · Adapter wrap** (new) — for API-relayed unsigned tx:
```
const { swap } = await externalApi.getSwap(quote);   // unsigned tx structure
return {
  status: 'pending_sign',
  unsigned_tx: { to: swap.to, data: swap.data, value: swap.value, chain: ... },
  description: ..., next_action: { tool: 'onchainos wallet contract-call' },
};
```

**Step 3b generation logic**: pick the matching template(s) per the Step 2b
scanner's signing-medium classification (multiple may apply).

### Gap 3 · Routing-conversion injection used a "violation count threshold"

v1.2 in practice: 23/14/4 violations → injected; 3/3 → not injected. This
threshold caused **`deployer` / `pay-with-any-token`** to skip injection.

**Hard rule**:
```
if requiredTools is non-empty → MUST inject the routing-conversion section,
                                regardless of violation count
if requiredTools is empty AND no signing/transaction keywords → skip the
                                upgrade entirely (see Gap 4)
```

### Gap 4 · Pure-doc / config / planning skills got irrelevant injections

v1.2 injected `[onchainOS dependency]` + `requiredTools: []` into 5 skills
that don't produce transactions: `uniswap-cca/configurator`,
`uniswap-driver/{liquidity,swap}-planner`,
`uniswap-hooks/{v4-hook-generator, v4-security-foundations}`. This created a
contradiction: "dependency declared + empty dependency list".

**Step 1.5 prefilter** (runs before form detection):

```
Scan the original SKILL.md for any "transaction signal" keyword:
  - sign / signature / unsigned_tx / transaction / broadcast
  - sendTransaction / writeContract / forge script --broadcast / cast send
  - tempo pay / onchainos wallet send / any wallet CLI write
  - pending_sign / onchainos wallet contract-call / send / sign-message

Any hit → proceed to form detection (full upgrade flow)
No hits → classify as "pure-doc skill" → skip upgrade, append at end of SKILL.md:

  > This skill is pure documentation / config / planning; it doesn't directly
  > produce on-chain transactions or signing messages, so it has no direct
  > integration with onchainOS. If downstream skills (deployer / executor
  > types) emit transactions, those downstream skills are responsible for
  > the pending_sign routing.
```

### Gap 5 · Repo-level batch upgrade

`Uniswap/uniswap-ai` is a monorepo (5 plugins × 10 skills). Single-skill
upgrades require 10 manual passes.

**Optional in v1.4**: support a "repo-level batch" trigger phrase:
```
"Run the upgrade flow on every skill under <monorepo-path>, output to <dest>"
→ Agent globs all SKILL.md → runs Step 1.5 prefilter on each → classifies →
  produces a consolidated migration table
```

---

## References

- `templates/` — three rendering templates (now used for fixed-section
  snippets only, not for from-scratch generation)
- `examples/my-dex-swap/` — complete sample of an upgrade output
- Upstream spec: third-party DApp OnchainOS integration quickstart, § 3
  "Skill integration"
