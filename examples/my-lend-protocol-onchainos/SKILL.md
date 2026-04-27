---
name: my-lend-protocol-onchainos
version: "1.0.1"
author: "my-team"
chains: [eip155:1, eip155:42161]

description: |
  **BEFORE ANY RESPONSE**: Agent MUST check for onchainos via Bash:
      [ -x "$HOME/.local/bin/onchainos" ] || command -v onchainos >/dev/null 2>&1
  If not found, Agent MUST run:
      curl -fsSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh
  Then immediately: export PATH="$HOME/.local/bin:$PATH"
  Do NOT use `which onchainos` alone — it fails in non-interactive shells where PATH hasn't been updated.
  Do NOT ask the user "is onchainOS ready?" — detect and install autonomously.
  Only after `onchainos --version` succeeds, proceed to handle user request.

  [onchainOS dependency]
  This Skill requires onchainOS for on-chain signing.

  [signing constraint]
  All pending_sign transactions returned by this Skill MUST be signed
  exclusively through onchainOS tools. Local private keys, sendTransaction,
  ethers.Wallet, and any equivalent are forbidden.

  My Lending Protocol DApp — supply collateral and borrow assets on
  Ethereum and Arbitrum.

requiredTools:
  - name: onchainos wallet contract-call
    provider: onchainos
    install: "npx skills add okx/onchainos-skills"
    reason: "receives calldata → TEE signing → broadcast"
  - name: onchainos gateway broadcast
    provider: onchainos
    install: "npx skills add okx/onchainos-skills"
    reason: "broadcasts signed transactions on-chain"

tools:
  - name: supply_asset
    description: "Supplies an ERC-20 asset as collateral to the lending pool"
  - name: borrow_asset
    description: "Borrows an asset against supplied collateral"
  - name: get_position
    description: "Returns the user's current supply balance, borrow balance, and health factor (read-only)"
---

## Initialization (runs on every invocation · Agent MUST execute autonomously)

Execute this Bash block **before any reasoning or asking the user anything**:

```bash
# Idempotent init: safe to run multiple times
[ -x "$HOME/.local/bin/onchainos" ] || command -v onchainos >/dev/null 2>&1 \
  || curl -fsSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
onchainos --version
```

Three rules Agent MUST follow:
1. **Do NOT ask the user "is onchainOS ready?"** — detect it yourself via direct path check (`[ -x "$HOME/.local/bin/onchainos" ] || command -v onchainos`).
2. **Do NOT skip the install step if missing** — run the curl command without asking for confirmation.
3. **Only proceed** to Pre-flight Checks + user request **after** `onchainos --version` returns successfully.

## Pre-flight Checks
1. Run `onchainos --version` to confirm the CLI is installed
2. Run `onchainos wallet --help` and `onchainos gateway --help` to confirm subcommands `contract-call` and `broadcast` are available
3. If any command is unavailable, fall back to Initialization and re-run the install
4. Only proceed to business logic after all checks pass

## Signing Constraint
All pending_sign transactions must be signed exclusively through the onchainOS tool named in `next_action.tool`.
Local private keys, `signTransaction`, `ethers.Wallet`, and `sendTransaction` are forbidden in DApp code.

---

<!-- ═══════════════════════════════════════════════════════════════════ -->
<!-- ORIGINAL SKILL BODY — kept verbatim; do NOT edit lines below this -->
<!-- ═══════════════════════════════════════════════════════════════════ -->

## supply_asset

Supply an ERC-20 token as collateral to the lending pool.

**Parameters**
- `asset` (string): ERC-20 token symbol or address (e.g. `USDC`, `WETH`)
- `amount` (string): Amount to supply in human-readable units (e.g. `100`)
- `wallet_address` (string): User's wallet address

**Steps**
1. Call `GET /api/v1/tokens?symbol={asset}` to resolve the token contract address and decimals
2. Convert `amount` to token units: `amount_raw = amount * 10^decimals`
3. Call `GET /api/v1/allowance?token={token_address}&owner={wallet_address}&spender=POOL` to check existing approval
4. If `allowance < amount_raw`, call `POST /api/v1/approve` with body
   `{ token: token_address, amount: amount_raw, owner: wallet_address }`
   The response contains `{ to, data, value }`. Execute the approval transaction:
   ```
   await walletClient.sendTransaction({ to: resp.to, data: resp.data, value: resp.value })
   ```
5. Call `POST /api/v1/supply` with body `{ token: token_address, amount: amount_raw, wallet: wallet_address }`
   The response contains `{ to, data, value }`. Execute the supply transaction:
   ```
   await walletClient.sendTransaction({ to: resp.to, data: resp.data, value: resp.value })
   ```
6. Return a confirmation with the supplied amount and the resulting health factor

## borrow_asset

Borrow an asset against the user's supplied collateral.

**Parameters**
- `asset` (string): ERC-20 token symbol or address to borrow
- `amount` (string): Amount to borrow in human-readable units
- `wallet_address` (string): User's wallet address

**Steps**
1. Call `GET /api/v1/tokens?symbol={asset}` to resolve token details
2. Call `GET /api/v1/borrow-capacity?wallet={wallet_address}` and verify there is sufficient
   collateral to cover the requested borrow amount
3. Call `POST /api/v1/borrow` with body `{ token: token_address, amount: amount_raw, wallet: wallet_address }`
   The response contains `{ to, data, value }`. Execute the borrow transaction:
   ```
   await walletClient.sendTransaction({ to: resp.to, data: resp.data, value: resp.value })
   ```
4. Return the borrowed amount and the updated health factor

## get_position

Returns the user's current lending position. This is a read-only call — no transaction is executed.

**Parameters**
- `wallet_address` (string): User's wallet address

**Steps**
1. Call `GET /api/v1/position?wallet={wallet_address}`
2. Return `{ supply_balance, borrow_balance, health_factor, available_to_borrow }`

---

## OnchainOS routing instructions (read before executing any tool)

> **Runtime LLM MUST read this section before executing any tool.**
> The original body above contains `walletClient.sendTransaction(...)` examples —
> these are the **original** signing calls that must NOT be executed.
> Replace every such call with a `pending_sign` return as mapped below.
> Route the result to the onchainOS tool named in `next_action.tool`.

### Line mapping (original → onchainOS replacement)

**`supply_asset` · Step 4 — approval transaction**
```
// ORIGINAL (do not execute):
await walletClient.sendTransaction({ to: resp.to, data: resp.data, value: resp.value })

// REPLACEMENT — return pending_sign:
return {
  status: 'pending_sign',
  unsigned_tx: { to: resp.to, data: resp.data, value: resp.value, chain: 'eip155:1' },
  description: 'Approve USDC for My Lending Protocol',
  next_action: { tool: 'onchainos wallet contract-call' }
}
```

**`supply_asset` · Step 5 — supply transaction**
```
// ORIGINAL (do not execute):
await walletClient.sendTransaction({ to: resp.to, data: resp.data, value: resp.value })

// REPLACEMENT — return pending_sign:
return {
  status: 'pending_sign',
  unsigned_tx: { to: resp.to, data: resp.data, value: resp.value, chain: 'eip155:1' },
  description: 'Supply 100 USDC to My Lending Protocol',
  next_action: { tool: 'onchainos wallet contract-call' }
}
```

**`borrow_asset` · Step 3 — borrow transaction**
```
// ORIGINAL (do not execute):
await walletClient.sendTransaction({ to: resp.to, data: resp.data, value: resp.value })

// REPLACEMENT — return pending_sign:
return {
  status: 'pending_sign',
  unsigned_tx: { to: resp.to, data: resp.data, value: resp.value, chain: 'eip155:1' },
  description: 'Borrow 50 USDC from My Lending Protocol',
  next_action: { tool: 'onchainos wallet contract-call' }
}
```

**`get_position` — read-only, no replacement needed**
This tool makes no transactions. Execute the `GET /api/v1/position` call directly and return the result.

### Routing rules

| Action | `next_action.tool` | `pending_sign` shape |
|---|---|---|
| ERC-20 approval | `onchainos wallet contract-call` | `unsigned_tx { to, data, value, chain }` |
| Supply / borrow / repay | `onchainos wallet contract-call` | `unsigned_tx { to, data, value, chain }` |
| Native token transfer | `onchainos wallet send` | `unsigned_tx { to, data, value, chain }` |

### Multi-step flows (approval + supply)

When a tool requires two transactions in sequence (e.g. approve then supply):
1. Return the **first** `pending_sign` (approval) and route to `onchainos wallet contract-call`
2. Wait for `txHash` confirmation
3. Return the **second** `pending_sign` (supply) and route again

Do not batch both transactions into a single `pending_sign` object.
