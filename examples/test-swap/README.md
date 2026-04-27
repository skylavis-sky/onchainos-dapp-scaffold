# test-swap

Test Swap DApp — scaffold smoke-test fixture.

Supported chains: eip155:1, eip155:137

## Install

```bash
npx skills add <your-org>/test-swap
```

This skill requires Onchain OS. On first use, the LLM will automatically run the install command in `## Pre-flight Checks`:

```bash
npx skills add okx/onchainos-skills
```

## First-time authentication (email wallet creation)

All on-chain signing is handled by Onchain OS inside a local TEE. This DApp never touches private keys or persists login state.

### Option A — Email OTP (recommended for individual users)

Onchain OS guides you through login on first signing call:

```bash
onchainos wallet login user@example.com     # sends OTP
onchainos wallet verify <6-digit-code>      # completes login
onchainos wallet status                     # confirm loggedIn: true
```

### Option B — API Key (automation / backend / CI)

```bash
export OKX_API_KEY=<your API Key>
export OKX_SECRET_KEY=<your Secret Key>
export OKX_PASSPHRASE=<your Passphrase>
onchainos wallet login
```

> To obtain credentials, visit the OKX Developer Portal (link provided by the technical team).

## Usage example

Trigger tools with natural language in your Agent:

> User: swap 100 USDC for ETH on Ethereum

The Agent follows this flow:

1. Calls the DApp tool (e.g. `my_build_swap`) to construct `unsigned_tx`
2. Tool returns `pending_sign` + `next_action.tool = 'onchainos wallet contract-call'`
3. Agent routes to Onchain OS `onchainos wallet contract-call`
4. Onchain OS signs + broadcasts inside the TEE and returns `txHash`

## Security

- This DApp never reads, stores, or transmits the user's private key, seed phrase, or keystore
- All `pending_sign` transactions are signed exclusively through Onchain OS
- `ethers.Wallet`, `signTransaction`, and `sendTransaction` are forbidden as alternative signing paths
