---
name: my-lend-protocol
version: "1.0.0"
author: "my-team"
chains: [eip155:1, eip155:42161]

description: |
  My Lending Protocol DApp — supply collateral and borrow assets on
  Ethereum and Arbitrum.

tools:
  - name: supply_asset
    description: "Supplies an ERC-20 asset as collateral to the lending pool"
  - name: borrow_asset
    description: "Borrows an asset against supplied collateral"
  - name: get_position
    description: "Returns the user's current supply balance, borrow balance, and health factor (read-only)"
---

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
