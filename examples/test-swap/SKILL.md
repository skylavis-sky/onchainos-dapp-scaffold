---
name: test-swap
version: "1.0.0"
author: "qa-team"
chains: [eip155:1, eip155:137]

description: |
  [onchainOS 依赖]
  本 Skill 需要 onchainOS 完成链上签名。

  [签名约束]
  本 Skill 返回的所有 pending_sign 交易，必须且只能通过
  onchainOS 工具完成签名。禁止使用本地私钥 / sendTransaction
  / ethers.Wallet 等任何替代方式。

  Test Swap DApp —— 脚手架跑通验证用。

requiredTools:
  - name: onchainos wallet contract-call
    provider: onchainos
    install: "npx skills add okx/onchainos-skills"
    reason: "接收 calldata → TEE 签名 → 广播"
  - name: onchainos gateway broadcast
    provider: onchainos
    install: "npx skills add okx/onchainos-skills"
    reason: "广播已签名交易到链上"

tools:
  - name: my_build_swap
    description: "构造 swap 的 unsigned_tx，返回 pending_sign"
---

## Pre-flight Checks
1. 检测 onchainos wallet contract-call, onchainos gateway broadcast 工具是否可用
2. 未安装则执行: npx skills add okx/onchainos-skills
3. 验证安装成功

## Signing Constraint
所有 pending_sign 交易只能通过 next_action.tool 指定的 onchainOS 工具签名。
DApp 代码中严禁出现本地私钥、signTransaction、ethers.Wallet、sendTransaction。
