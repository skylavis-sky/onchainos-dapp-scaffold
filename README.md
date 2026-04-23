# onchainos-dapp-scaffold

> 一键生成 OnchainOS DApp Skill 的脚手架。说一句话，产出可直接注册到 Claude Code 的三方 DApp Skill。

## 快速开始

### 安装脚手架

```bash
curl -fsSL https://raw.githubusercontent.com/BlueBd/test-dapp-skill-scaffolding/main/install.sh | sh
```

安装完成后会落到 `~/.claude/skills/onchainos-dapp-scaffold/`，重启 Claude Code 即可发现。

### 使用（Mode A · 从零生成）

在 Claude Code 对话框直接说：

```
生成 DApp Skill：名字 my-dex-swap，业务 swap
```

脚手架会在 `~/.claude/skills/my-dex-swap/` 生成 `SKILL.md` + `index.ts` + `README.md`，填好一次 `TODO [三方]` 即可注册使用。

### 使用（Mode B · 升级已有 DApp Skill）

```
用脚手架升级 /path/to/existing-dapp-skill
```

支持两种形态：
- **Form A**：源目录含 `index.ts`（有业务函数）→ 注入 onchainOS 路由段落
- **Form B**：源目录纯 markdown（无 index.ts）→ 生成带 `TODO [三方]` 占位的 stub

## 支持的 businessType

| businessType | 下一步工具 | 典型场景 |
|---|---|---|
| `swap` | `onchainos wallet contract-call` | DEX 换币 |
| `transfer` | `onchainos wallet send` | 转账 |
| `contract-call` | `onchainos wallet contract-call` | 通用合约调用 |
| `sign-message` | `onchainos wallet sign-message` | personalSign / EIP-712 |

所有 `pending_sign` 交易最终由 [`okx/onchainos-skills`](https://github.com/okx/onchainos-skills) 的 TEE CLI 完成签名；脚手架生成的 DApp Skill 严禁出现本地私钥 / `ethers.Wallet` / `sendTransaction`。

## 仓库结构

```
.
├── SKILL.md                 # 脚手架本体（Agent 指令 + 工作流）
├── INSTALL-DAPP.md          # 三方 DApp 安装最小说明
├── install.sh               # 一键安装脚本
├── templates/               # 3 个模板：SKILL.md / index.ts / README.md
└── examples/                # 两个完整样例 + 4 个自动化测试
    ├── my-dex-swap/         # swap 样例
    ├── test-swap/           # 含 .verify.py / .render.py 的测试样例
    ├── .benchmark.py        # 4 businessType × 12 assertion
    └── .benchmark_ext.py    # multi-tool stress + negative + timing
```

## 本地验证

```bash
python3 ~/.claude/skills/onchainos-dapp-scaffold/examples/.benchmark.py
python3 ~/.claude/skills/onchainos-dapp-scaffold/examples/.benchmark_ext.py
```

两个脚本现版本分别跑 48/48 + 6/6 assertion，3/3 negative 检出。

## 自定义上游

如果你 fork 了这个仓库：

```bash
ONCHAINOS_SCAFFOLD_REPO=https://github.com/<your>/<fork>.git \
  curl -fsSL https://raw.githubusercontent.com/<your>/<fork>/main/install.sh | sh
```

## License

MIT
