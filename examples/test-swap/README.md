# test-swap

Test Swap DApp —— 脚手架跑通验证用。

支持的链：eip155:1, eip155:137

## 安装

```bash
npx skills add <your-org>/test-swap
```

本 Skill 依赖 onchainOS。首次使用时 LLM 会根据 `## Pre-flight Checks` 自动执行：

```bash
npx skills add okx/onchainos-skills
```

## 首次使用认证（邮箱创建钱包）

所有链上签名通过 onchainOS 在本地 TEE 完成。本 DApp 不接触私钥、不保存登录状态。

### 方式 A | 邮箱 OTP（推荐个人用户）

首次调用签名工具时 onchainOS 自动引导：

```bash
onchainos wallet login user@example.com     # 发送验证码
onchainos wallet verify <6-digit-code>      # 完成登录
onchainos wallet status                     # 验证 loggedIn: true
```

### 方式 B | API Key（自动化 / 后端 / CI）

```bash
export OKX_API_KEY=<你的 API Key>
export OKX_SECRET_KEY=<你的 Secret Key>
export OKX_PASSPHRASE=<你的 Passphrase>
onchainos wallet login
```

> 凭证申请入口：OKX 开发者门户（链接由技术团队提供）。

## 使用示例

在 Agent 中以自然语言触发工具：

> 用户：帮我 swap 100 USDC for ETH on Ethereum

Agent 会按以下流程工作：

1. 调用本 DApp 工具（如 `my_build_swap`）构造 `unsigned_tx`
2. 工具返回 `pending_sign` + `next_action.tool = 'onchainos wallet contract-call'`
3. Agent 路由到 onchainOS 的 `onchainos wallet contract-call`
4. onchainOS 在 TEE 内签名 + 广播，返回 `txHash`

## 安全说明

- 本 DApp 不在任何时机读取、存储或传输用户私钥、助记词、keystore
- 所有 pending_sign 交易只能经 onchainOS 签名
- 禁用 `ethers.Wallet` / `signTransaction` / `sendTransaction` 等替代路径
