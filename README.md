# onchainos-dapp-scaffold

> Scaffolding for OnchainOS DApp Skills. Take an **existing** DApp skill and have the scaffold upgrade it into one that routes signing/broadcasting through OnchainOS.

OnchainOS is a local TEE-based CLI wallet — the agent never touches the user's private key. Your DApp constructs the unsigned transaction; OnchainOS handles signing and broadcasting inside the TEE. See [GUIDE.md](GUIDE.md) for full integration details.

## Quick start

### Install the scaffold

```bash
curl -fsSL https://raw.githubusercontent.com/okx/dapp-connect-agenticwallet/main/install.sh | sh
```

Installs to `~/.agents/skills/onchainos-dapp-scaffold/` (Claude Code, OpenClaw, Codex, Cursor, etc. all pick it up). Restart your AI agent after install.

### Use it

Bring an existing DApp skill — your own, or a fork of one — and ask your agent:

```
Use the scaffold to upgrade /path/to/your-existing-dapp-skill
```

The scaffold auto-detects the source form and `businessType`. To override detection, append it explicitly: `..., businessType=swap`.

The scaffold supports two source forms:

| Source form | Layout | What the scaffold does |
|-------------|--------|------------------------|
| **Form A** | `SKILL.md` + `index.ts` with exported business functions | Wraps each transaction/signing tool with a `pending_sign` shell; read-only tools pass through. |
| **Form B** | `SKILL.md` only (or `index.ts` with no exports) | Appends a routing conversion section to `SKILL.md` that maps each original tool's signing/transaction lines to `pending_sign` returns; no code is generated. |

Output lands at `<your-skill>-onchainos/` adjacent to the input skill (e.g. `~/.agents/skills/<your-skill>-onchainos/`). Original skill is untouched, so you can roll back any time.

> The scaffold deliberately does **not** support generating a skill from scratch.
> Bring an existing DApp skill — the scaffold's job is to convert, not to invent.

## Testing guide

End-to-end test steps with three sample DApps (Uniswap / GMX / Morpho) are in **[GUIDE.md](GUIDE.md)**:

- Pick a test endpoint and set environment variables
- Clone the scaffold + the DApp skill from GitHub
- Run the upgrade and verify the output
- Walk through typical scenarios per `businessType`

## Supported businessTypes

| businessType | Next-step tool | `pending_sign` shape | Typical use |
|---|---|---|---|
| `swap` | `onchainos wallet contract-call` | `unsigned_tx { to, data, value, chain }` | DEX swaps |
| `transfer` | `onchainos wallet send` | `unsigned_tx { to, data, value, chain }` | Native / ERC-20 transfers |
| `contract-call` | `onchainos wallet contract-call` | `unsigned_tx { to, data, value, chain }` | Generic contract calls |
| `sign-message` | `onchainos wallet sign-message` | `message` (no `unsigned_tx`) | personalSign / EIP-712 |

> `onchainos gateway broadcast` appears as a `requiredTools` entry in generated skills — it is a dependency chained internally by `contract-call` / `send`, not a tool you call directly.

All `pending_sign` transactions are signed by the [`okx/onchainos-skills`](https://github.com/okx/onchainos-skills) TEE CLI. Generated skills must **not** contain local private keys, `ethers.Wallet`, `signTransaction`, or any other local-signing code — the scaffold rejects upgrades that detect these.

> **EIP-712 precision**: all `uint*/int*` fields in a `sign-message` payload must be serialized as strings via `BigInt(String(v)).toString()` to avoid silent precision loss above 2^53−1. See [GUIDE.md Appendix C](GUIDE.md#appendix-c) for details.

## Supported chains

| Network | Status | Chains |
|---|---|---|
| EVM | Supported | Ethereum, Polygon, BNB Chain, Arbitrum One, Base, Optimism, Avalanche C, Fantom, Blast, Scroll, Sonic, zkSync Era, Linea, Monad, Conflux, X Layer |
| Bitcoin | Supported | Bitcoin (native + BRC-20) |
| Solana | Supported | Solana |

## Repo layout

```
.
├── SKILL.md                 # Scaffold itself (agent instructions + workflow)
├── INSTALL-DAPP.md          # Minimal install notes for third-party DApps
├── install.sh               # One-line installer
├── templates/               # 3 templates: SKILL.md / index.ts / README.md
└── examples/                # 2 complete samples + 4 automated tests
    ├── my-dex-swap/         # Swap sample
    ├── test-swap/           # Sample with .verify.py / .render.py tests
    ├── .benchmark.py        # 4 businessTypes × 12 assertions
    └── .benchmark_ext.py    # Multi-tool stress + negative + timing
```

## Local verification

```bash
python3 ~/.agents/skills/onchainos-dapp-scaffold/examples/.benchmark.py
python3 ~/.agents/skills/onchainos-dapp-scaffold/examples/.benchmark_ext.py
```

Current benchmarks: 48/48 + 6/6 assertions, 3/3 negative cases caught.

## Custom upstream

If you've forked the scaffold:

```bash
ONCHAINOS_SCAFFOLD_REPO=https://github.com/<your>/<fork>.git \
  curl -fsSL https://raw.githubusercontent.com/<your>/<fork>/main/install.sh | sh
```

## License

MIT
