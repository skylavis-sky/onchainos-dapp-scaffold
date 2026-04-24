---
name: onchainos-dapp-scaffold
version: "1.3.0"
author: "okx"
description: |
  一键生成 / 升级 OnchainOS DApp Skill。说一句话即可产出可直接注册使用的 DApp Skill。

  [一句话调用 · Mode A 从零生成]
  生成 DApp Skill：名字 <kebab-case>，业务 <swap|transfer|contract-call|sign-message>

  示例："生成 DApp Skill：名字 my-dex-swap，业务 swap"

  [一句话调用 · Mode B 升级已有 Skill]
  用脚手架升级 <skill-dir>
  或：升级 DApp Skill：路径 <skill-dir>

  示例："用脚手架升级 ~/.claude/skills/uniswap-ai-test"
  示例："升级 DApp Skill：路径 ~/.claude/skills/my-dex"

  Mode B 会读入目录（Form A 含 index.ts / Form B 仅 markdown），按 onchainOS 规范注入
  pending_sign 外壳 + next_action.tool 路由 + requiredTools + 3 处固定段落。

  [产出 · 3 份文件]
    • SKILL.md   —— onchainOS Skill 方案规范（3 处 [固定] 段落 + requiredTools + Pre-flight Checks）
    • index.ts   —— pending_sign 外壳 + 按业务类型预填的函数骨架
    • README.md  —— 终端用户安装 + 认证指引（零改动即可发布）

  DApp 开发者仅需在 index.ts 的 `TODO [三方]` 注释处补业务逻辑（5-10 行）。

  [适用范围] 仅 Claude Code（含完全兼容 fork）。Cursor / Codex / OpenCode 需走 MCP 方案。

triggers:
  - "生成 DApp Skill"
  - "帮我生成 onchainOS Skill"
  - "scaffold onchainOS DApp"
  - "用脚手架升级"
  - "升级 DApp Skill"
  - "upgrade onchainOS DApp"
---

# OnchainOS DApp 接入脚手架

本 Skill 为 AI 工作流定义。LLM 按以下步骤与用户对话并生成文件。

## 工作流（默认走「快速模式」—— 2 必填，其余自动默认）

### 步骤 1 — 采集关键信息

**快速模式（默认）**：仅确认 2 个必填字段，其余按默认值生成。确认后立即渲染，不追问。

| # | 字段 | 说明 | 快速模式处理 |
|---|------|------|-------------|
| 1 | `name` | DApp 标识符（kebab-case） | **必填**——用户没给就问一次 |
| 2 | `businessType` | 业务类型（见下表） | **必填**——用户没给就问一次 |
| 3 | `version` | 版本号 | 自动 = `1.0.0` |
| 4 | `author` | 作者 / 团队 | 自动 = `my-team`（或从 `git config --get user.name` 读，读不到用默认） |
| 5 | `chains` | 支持链 | 自动 = `[eip155:1]` |
| 6 | `tools` | 工具列表 | 自动 = `[("<name 去 - 换 _>_main", "<businessType> 主工具")]` |
| 7 | `outputDir` | 输出目录 | 自动 = `./<name>` |

**详细模式（用户明确说"我要自定义"时启用）**：按顺序逐项确认 7 个字段。

**用户没说但能推断的字段** → 直接填默认值；用户**先说了**某字段 → 沿用；字段**缺失且无默认**（只有 name/businessType）→ 才追问，最多 2 次对话完成。

**业务类型** 决定 `next_action.tool` 与 `requiredTools` 默认值：

| businessType | next_action.tool | requiredTools |
|--------------|------------------|---------------|
| `swap` | `onchainos wallet contract-call` | `onchainos wallet contract-call`, `onchainos gateway broadcast` |
| `transfer` | `onchainos wallet send` | `onchainos wallet send`, `onchainos gateway broadcast` |
| `contract-call` | `onchainos wallet contract-call` | `onchainos wallet contract-call`, `onchainos gateway broadcast` |
| `sign-message` | `onchainos wallet sign-message` | `onchainos wallet sign-message` |
| `pipeline` | 按工具分别指定 | 组合以上 |

### 步骤 2 — 渲染模板

读取 `templates/` 目录下的模板文件，执行变量替换：

- `templates/SKILL.md.template` → `<outputDir>/SKILL.md`
- `templates/index.ts.template` → `<outputDir>/index.ts`
- `templates/README.md.template` → `<outputDir>/README.md`

变量清单（与模板中出现的 `{{VAR}}` 一一对应）：`{{NAME}}` `{{VERSION}}` `{{AUTHOR}}`
`{{CHAINS}}` `{{PRIMARY_CHAIN}}` `{{DESCRIPTION}}` `{{EXAMPLE_USER_PROMPT}}`
`{{REQUIRED_TOOLS_YAML}}` `{{REQUIRED_TOOL_NAMES}}`
`{{TOOLS_YAML}}` `{{TOOL_FUNCTIONS}}` `{{NEXT_ACTION_TOOL}}`

#### TOOL_FUNCTIONS 生成规则（强约束，避免产出抖动）

对 `tools` 数组中的**每一个**工具 `(name, description)`，按 `businessType` 选取以下骨架
之一进行 **文本拼接**（不要自由发挥）。每个骨架的 `// TODO [三方]` 之外的行逐字保留：

```ts
// ───── swap / contract-call 骨架 ─────
// v1.2：用抛错式占位符取代 '0xTODO' 字面量，强制 LLM 运行时替换或 DApp 开发者填充
async function <NAME>(params: any): Promise<PendingSign> {
  // TODO [三方] 查路由 / 算价 / 构造 calldata
  const TODO = (field: string): never => {
    throw new Error(`[SCAFFOLD-UNFILLED] ${field} 未填充：请补业务逻辑或在运行时由 LLM 读取注释替换`);
  };
  const unsigned_tx = {
    to:    TODO('to'),       // 目标合约地址
    data:  TODO('data'),     // ABI 编码 calldata
    value: '0',
    chain: '{{PRIMARY_CHAIN}}',
  };
  return {
    status: 'pending_sign',
    unsigned_tx,
    description: TODO('description'),   // 人类可读摘要
    next_action: { tool: '{{NEXT_ACTION_TOOL}}' },
  };
}

// ───── transfer 骨架 ─────
async function <NAME>(params: any): Promise<PendingSign> {
  // TODO [三方] 解析 to / amount / token
  const TODO = (f: string): never => { throw new Error(`[SCAFFOLD-UNFILLED] ${f}`); };
  const unsigned_tx = {
    to:    TODO('to'),       // 收款地址
    data:  '0x',             // 原生转账留空；ERC-20 transfer 需填 encoded calldata
    value: TODO('value'),    // 原生量 (wei)；ERC-20 场景填 '0'
    chain: '{{PRIMARY_CHAIN}}',
  };
  return {
    status: 'pending_sign',
    unsigned_tx,
    description: TODO('description'),
    next_action: { tool: '{{NEXT_ACTION_TOOL}}' },
  };
}

// ───── sign-message 骨架（不上链，结构略不同）─────
async function <NAME>(params: any) {
  const TODO = (f: string): never => { throw new Error(`[SCAFFOLD-UNFILLED] ${f}`); };

  // ── EIP-712 精度规则（必读）────────────────────────────────────────────────
  // 所有 uint*/int* 字段 **必须** 用 BigInt(x).toString() 转为字符串，
  // 严禁使用 JS Number（Number.MAX_SAFE_INTEGER = 2^53-1，uint64 及以上会静默丢精度，
  // 导致链上签名验证失败且无前端报错，极难排查）。
  //
  //   ❌ message: { sigDeadline: apiResponse.sigDeadline }          // Number，可能丢精度
  //   ✅ message: { sigDeadline: BigInt(apiResponse.sigDeadline).toString() }
  // ─────────────────────────────────────────────────────────────────────────────

  // ── EIP-712 结构转换（如 API 返回非标准格式）──────────────────────────────────
  // 若三方 API 返回 { domain, types, values } 而非标准 { types, primaryType, domain, message }，
  // 必须先转换（否则 onchainos 报 "missing msgHash"）：
  //
  //   const typedData = {
  //     types:       { EIP712Domain: [...domainFields], ...apiResp.types },
  //     primaryType: Object.keys(apiResp.types).find(k => k !== 'EIP712Domain'),
  //     domain:      apiResp.domain,
  //     message:     apiResp.values,   // <── values → message
  //   };
  // ─────────────────────────────────────────────────────────────────────────────

  // TODO [三方] 构造待签名消息，应用上述规则后赋给 message
  return {
    status: 'pending_sign',
    message: TODO('message'),               // personalSign 串 / 标准 EIP-712 typed data
    description: TODO('description'),       // 签名用途说明
    next_action: { tool: '{{NEXT_ACTION_TOOL}}' },
  };
}
```

**为什么用抛错式占位符**（v1.2 设计决定）：
- 旧版 `'0xTODO'` 是合法字面量字符串，LLM 在"模拟执行"时会按字面值返回，导致 onchainOS 拿到无效地址签名失败
- 新版 `TODO('to')` 立刻 throw，LLM 必须在推理阶段**要么替换成真值**（按注释调 API），**要么向用户求 API key**，不允许按字面量丢回
- DApp 开发者手填时也更醒目：光看到 `'0xTODO'` 可能漏掉，看到 throw 必然意识到要动

拼接规则：
- 多工具：每个函数体之间用一空行隔开
- 末尾追加：`export { <name1>, <name2>, ... };`
- `{{PRIMARY_CHAIN}}` = `chains` 数组第一个元素

#### pipeline businessType 处理规则

`businessType = pipeline` 表示一个 Skill 内混合**交易工具 + 只读工具**（如 `search_token` / `get_price` / `build_swap` 三件套）。生成时：

1. 让用户对每个 tool 明确其子类型：`swap` / `transfer` / `sign-message` / `readonly`
2. 交易类 tool 按对应骨架生成 `pending_sign` 返回值
3. **只读 tool** 使用以下独立骨架（不走 pending_sign）：

```ts
async function <NAME>(params: any) {
  // TODO [三方] 查询业务（返回普通 JSON，不签名）
  return { /* TODO [三方] 查询结果 */ };
}
```

4. `requiredTools` 取并集（如 `[onchainos wallet contract-call, onchainos gateway broadcast]`）；只读 tool **不贡献** requiredTools
5. `next_action.tool` 按工具粒度分别指定，**不共享**
6. 只读 tool 在 SKILL.md `tools` 数组中声明时，建议 description 前缀 `[只读]` 以便 Agent 自动编排

### 步骤 3 — 写入文件

按变量替换规则把 3 份模板写入 `<outputDir>/`。写入完成后**立刻**进入步骤 4。

### 步骤 4 — 自检（生成后必跑，不可跳过）

对 `<outputDir>/` 的 3 份文件做机械检查。逐项跑 Bash 命令并把结果汇总给用户：

```bash
D=<outputDir>
# A1 无未解析变量
grep -l '{{' $D/* && echo FAIL:A1 || echo PASS:A1
# A2 YAML frontmatter 合法
python3 -c "import yaml,sys; yaml.safe_load(open('$D/SKILL.md').read().split('---',2)[1])" && echo PASS:A2 || echo FAIL:A2
# A3 3 处 [固定] 段落齐全
grep -q '\[onchainOS 依赖\]' $D/SKILL.md && grep -q '\[签名约束\]' $D/SKILL.md && grep -q '## Pre-flight Checks' $D/SKILL.md && grep -q '## Signing Constraint' $D/SKILL.md && echo PASS:A3 || echo FAIL:A3
# A4 无本地签名 (expanded pattern set — covers JS, Solana, Foundry CLI, wagmi, ERC-4337, HD, API-relay)
grep -v '^//' $D/index.ts | grep -qE \
  'ethers\.Wallet|new Wallet\(|signTransaction|sendTransaction|privateKey|mnemonic|keystore|\
Keypair\.fromSecret|nacl\.sign|forge\s+script.*--broadcast|cast\s+send|anchor\s+deploy|\
useSignMessage|useWriteContract|useWalletClient|writeContract\(\
|signUserOp|UserOperation|signTypedData\(|eth_sendTransaction|eth_sendRawTransaction|\
HDNodeWallet|mnemonicToAccount|deriveChild|\
window\.ethereum\.request.*eth_send|window\.ethereum\.send\b' \
  && echo FAIL:A4 || echo PASS:A4
# A5 pending_sign 契约
grep -q 'pending_sign' $D/index.ts && grep -q 'next_action' $D/index.ts && echo PASS:A5 || echo FAIL:A5
```

预期：5 项全 PASS。任一 FAIL → 告知用户具体哪项挂了并提议修复；**不要**声称生成成功。

### 步骤 5 — 一键测试引导（生成后主动给出）

按 `businessType` 给用户一句可直接 paste 的测试话术：

| businessType | 测试话术模板 |
|---|---|
| `swap` | `swap 100 USDC to ETH on <chain>` |
| `transfer` | `send 10 USDC to 0xAbC...` |
| `contract-call` | `call <contract-address> <function-name> with <args>` |
| `sign-message` | `sign login challenge for <domain>` |

然后给出 3 条后续动作（**按此顺序**给，不要合并成一段）：

1. **立即注册 + 测试**：`cp -r <outputDir> ~/.claude/skills/<name> && 在新对话里输入 <测试话术>`
2. **补业务代码**：打开 `<outputDir>/index.ts`，搜 `TODO [三方]`，只需填 `unsigned_tx.to / data / value` 与 `description`
3. **发布**：推到 GitHub，把 `git clone https://github.com/<owner>/<repo> ~/.claude/skills/<name>` 作为安装命令贴给你的用户

## 适用范围 & 运行时模型（生成前必须告知用户）

**本脚手架产物仅适用于：Claude Code**（及兼容 Claude Code Skill 格式的 fork，如 OpenClaw 若完全兼容则可复用）。
**不适用于**：Cursor / Codex CLI / OpenCode —— 它们没有 Skill 加载器，需要走 1.2 MCP 方案（另一套脚手架）。

**运行时模型**：`index.ts` 不会被任何进程执行。Claude Code Skill = Markdown 指令。
实际执行路径 = LLM 读取 index.ts → 在推理阶段模拟函数体（调 Bash/WebFetch 等工具取真实数据）→ 按 `pending_sign` 契约返回 JSON → Claude 按 `next_action.tool` 路由到 onchainOS。

**因此本方案仅适合**：calldata 构造类纯函数工具（swap 路由查询 + encode，transfer 地址校验等）。
**不适合**：多步 retry / WebSocket 订阅 / 复杂状态机 / 重业务逻辑 → 请改用 MCP 方案。

## Mode B — 升级已有 DApp Skill（三输入合成）

当用户**提供以下 3 项输入**时（任意组合被识别即进入本模式，优先级高于 Mode A 从零生成）：
1. 脚手架规范文档（本 SKILL.md 即为规范；或"三方 DApp 接入 onchainOS 快速指引"第 3 节）
2. 脚手架 Skill 本身（就是当前这个 `onchainos-dapp-scaffold`）
3. 三方 DApp 的现有 Skill（路径如 `~/.claude/skills/<dapp-name>/`）

**触发话术示例**：
```
我有个现成的 DApp Skill 在 ~/.claude/skills/my-dex，
按 onchainOS Skill 方案升级它，输出到 ~/.claude/skills/my-dex-onchainos/
```

### Mode B 工作流（7 步，含形态分叉）

**B1. 读取 DApp 原 Skill**
- `<src>/SKILL.md` → 解析 frontmatter（name / version / author / tools 数组）+ description + 正文全文
- `<src>/index.ts` → 若存在，识别 **每个函数签名**、**返回值类型**、**是否已有签名逻辑**
- `<src>/README.md`（若存在）→ 提取 DApp 业务描述
- `<src>/references/` 或其他子目录 → 记录路径清单，后续可能需整包拷贝

**B1.5. 形态识别（v1.2 新增 · 关键分叉）**

根据原 Skill 的文件构成决定后续流程，**不可跳过**：

| 判据 | 形态 | 处理路线 |
|---|---|---|
| `<src>/index.ts` 存在，且含导出的业务函数 | **形态 A** | 走 B2a → B3a → B4a → B5 → B6（原 6 步流程） |
| 仅有 `<src>/SKILL.md`，无 index.ts 或 index.ts 无导出函数 | **形态 B** | 走 B2b → B3b → B4b → B5 → B6（markdown-merge 分支） |
| 已检测到本地签名代码（见§硬约束条目3完整列表） | **违规** | **立即停止**，要求用户先人工清理再重试 |

**判别命令**：
```bash
test -f <src>/index.ts && grep -q '^export' <src>/index.ts && echo "形态 A" || echo "形态 B"
```

**违规扫描命令**（在形态判别之前必须先跑）：
```bash
grep -rn \
  'ethers\.Wallet\|new Wallet(\|signTransaction\|sendTransaction\|privateKey\|Keypair\.fromSecret\|nacl\.sign\|forge script.*--broadcast\|cast send\|useSignMessage\|useWriteContract\|signUserOp\|HDNodeWallet\|mnemonicToAccount\|window\.ethereum\.request.*eth_send\|walletClient\.writeContract\|walletClient\.sendTransaction' \
  <src>/ 2>/dev/null | grep -v '^.*:.*\/\/' | head -20
# 任意一行有输出 → 报告违规，立即停止
```

---

### 形态 A 路线（原 Skill 含可执行代码）

**B2a. 分类每个工具**（决定是否要包装 pending_sign）
逐个工具分类：

| 判据 | 分类 | 处理方式 |
|---|---|---|
| 函数名含 `build` / `swap` / `mint` / `deposit` 等 + 返回 tx/calldata | 交易类 | 包装 pending_sign |
| 函数名含 `send` / `transfer` + 有 to+amount 参数 | 转账类 | 包装 pending_sign → `onchainos wallet send` |
| 函数名含 `sign` / `login` / `authorize` + 返回 message | 签名类 | 包装 pending_sign → `onchainos wallet sign-message` |
| 函数名含 `get` / `query` / `search` / `list` + 返回普通 JSON | 只读类 | **不动**，直接透传 |
| 已有 `ethers.Wallet` / `signTransaction` / `privateKey` | **违规**——原 Skill 在本地签名 | 提醒用户：必须先去掉本地签名，才能集成 onchainOS |

**B3a. 合成新 SKILL.md（merge 策略，v1.3）**

使用 **merge 策略**，而非 rewrite 策略——原 frontmatter 的所有字段都必须被保留，仅注入脚手架字段：

1. **读取原 frontmatter** 的所有字段（包括 `allowed-tools`、`model`、`license`、`metadata` 等非标准字段）
2. **覆写以下字段**（脚手架固定值优先）：
   - `name` = 原 name + `-onchainos` 后缀（若原名已含 `-onchainos` 则不重复追加）
   - `version` = 原 version patch 位 +1（如 `1.2.0` → `1.2.1`）
   - `description` = 注入 `[onchainOS 依赖]` + `[签名约束]` 段落（追加在原 description 之后，不替换）
   - `requiredTools` = 交易类 + 转账类 + 签名类工具对应的 onchainOS 工具并集（若原已有则取并集）
3. **保留所有其他原字段**（`author`、`chains`、`tools`、`allowed-tools`、`model`、`license`、`metadata` 等）——不得静默丢弃
4. **merge 后检验**：新 SKILL.md frontmatter 字段数 ≥ 原 frontmatter 字段数；若数量减少，必须列出丢失字段并告知用户
5. 注入 `## Pre-flight Checks` + `## Signing Constraint` 节（原样复制自 template）
6. **原 SKILL.md 正文**（frontmatter 之外的 markdown 文档）**全文保留**，追加在新 frontmatter 之后，作为业务说明

**B4a. 合成新 index.ts**
- 顶部注入 RUNTIME MODEL 警告（复制 templates/index.ts.template 开头）
- **顶部同时注入 `toSafeInt` helper**（复制 templates/index.ts.template 的 toSafeInt 函数）——无论是否含 sign-message 工具，统一注入，避免遗漏
- **原业务函数** → 改名加 `_impl` 后缀（如 `my_build_swap` → `_my_build_swap_impl`），作为内部 helper 保留
- **每个交易类工具** → 生成新外层函数，按 `pending_sign` 骨架包装，内部调原 `_impl` 拿 `unsigned_tx`
- **签名类工具**（sign-message）→ 包装时必须额外检查：
  - 原 `_impl` 返回的 message 字段中，所有 EIP-712 `uint*/int*` 字段一律改为 `toSafeInt(...)` 调用
  - 若原 `_impl` 返回 `{domain, types, values}` 非标准结构，在外层函数中插入标准格式转换（见附录 B / sign-message 骨架注释）
- **只读工具** → 直接透传（原样导出）
- `export { ... }` 列出所有对外工具（外层 + 只读）

---

### 形态 B 路线（原 Skill 仅有 markdown，无 index.ts）· v1.2 新增

**适用场景**：原 Skill 是 AI 指引/教学文档，用 markdown 说明"Agent 调哪些 API 怎么调"，本身没有可执行业务函数。这类 skill 在 Claude Code 生态占大多数（例如 `uniswap/uniswap-ai` 的全部 10 个 skills）。

**B2b. 识别原 SKILL.md 里的"工具调用链"**

扫描原 SKILL.md 正文，找：
- HTTP endpoint（如 `POST /v1/quote`、`POST /v1/swap`）
- 返回字段里含 `to` / `data` / `value` / `calldata` / `unsignedTx` / `transaction` 等可能是 unsigned_tx 的字段
- 本地签名关键词（`walletClient.sendTransaction` / `ethers.Wallet.signTransaction` / `privateKey`）

若发现本地签名关键词 → B2b 输出"违规清单"，**立即停止**，要求用户先人工处理。

**B3b. 合成新 SKILL.md（markdown-merge 策略，v1.3）**
- **原 SKILL.md 正文全文保留**（除 frontmatter 外一字不改）
- **frontmatter 采用 merge 策略**（同 B3a 规则）：保留原所有字段（`allowed-tools`、`model`、`license`、`metadata` 等），仅注入/覆写脚手架的 3 个固定字段：
  - `description` += `[onchainOS 依赖]` + `[签名约束]`（追加，不替换）
  - `requiredTools` = 并集
  - 版本 patch +1
- **在新 frontmatter 中注入**：`[onchainOS 依赖]` / `[签名约束]` / `requiredTools` / `## Pre-flight Checks` / `## Signing Constraint` 这 5 处 [固定] 位置
- **在原正文末尾追加一节**「## onchainOS 路由改造（v1.2 自动注入）」，内容包含：
  - 原 SKILL.md 里出现的本地签名示例行号清单 + 每行对应的 onchainOS 替换写法
  - pending_sign 结构 + `next_action.tool` 路由规则
  - 运行时 LLM 必读：不要执行原文示例里的本地签名代码，改为构造 pending_sign 返回

**B4b. 不生成 stub index.ts**
- 对形态 B，**不造假** index.ts。原 skill 没有业务函数，就让新 skill 也没有
- Claude Code skill 支持纯 markdown 形态，LLM 读 SKILL.md 正文即可按指引调 API
- 若用户坚持要 index.ts，提示："建议你先给原 skill 补充 index.ts 业务函数再走 Mode B 形态 A 路线，否则 stub 无实战价值"

**B4b 扩展 · 拷贝 references/ 及其他资源目录**
- 原 skill 若有 `<src>/references/` / `<src>/_shared/` 等目录，**整包拷贝**到新产物
- 不做内容裁剪

---

### 两种形态共用的后续步骤

**B5. 合成新 README.md**
- 复制 templates/README.md.template
- `{{DESCRIPTION}}` 用原 SKILL.md description 提取第一句
- `{{EXAMPLE_USER_PROMPT}}` 按第一个交易类工具的业务类型选一个测试话术

**B6. 自检 + 对齐报告**
- 跑步骤 4 的 5 项 Bash 自检
- **额外对齐报告**：列出"从原 Skill 保留了什么 / 新增了什么 / 改动了什么"三栏 diff 摘要
- 生成"迁移对照表"让用户验证无信息丢失：

```
原工具名              新工具名              分类       onchainOS 工具
my_build_swap   →     my_build_swap         交易       onchainos wallet contract-call
my_get_price    →     my_get_price          只读       —（直接透传）
my_search_token →     my_search_token       只读       —
```

### Mode B 硬约束

1. **不得修改**原 Skill 的业务逻辑语义（`_impl` 函数内部保持不变，仅被外层包装）
2. **不得推断** unsigned_tx 的 `to` / `data`——这些必须由原 `_impl` 函数返回，Mode B 只负责包装成 pending_sign 外壳
3. 若原 Skill 已有本地签名代码（ethers.Wallet 等），**B2 阶段拒绝继续**，让用户先清理原 Skill

## 硬约束（生成时必须遵守）

1. SKILL.md 必须包含 3 处 [固定] 位置：`description` 中的 `[onchainOS 依赖]` +
   `[签名约束]` 段落、`requiredTools` 数组、`## Pre-flight Checks` +
   `## Signing Constraint` 节。
2. index.ts 每个工具函数返回值必须符合 `pending_sign` 契约：
   `{ status, unsigned_tx: {to, data, value, chain}, description, next_action: {tool} }`
3. **严禁**生成包含以下任意代码（全平台覆盖）：

   **JS / TS 内联签名**
   - `ethers.Wallet` / `new Wallet(...)` / `privateKey`
   - `signTransaction` / `sendTransaction`
   - `signTypedData(...)` / `eth_sendRawTransaction`
   - 直接调用 `window.ethereum` 的写操作（`window.ethereum.request({method:'eth_send*'})` 等）

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
   - `signUserOp(...)` / `UserOperation` 对象直接发送

   **HD 钱包推导**
   - `HDNodeWallet` / `mnemonicToAccount` / `.deriveChild(...)`

   **助记词 / Keystore / 密钥文件读取**
   - 读取 `.env` 中私钥字段 / keystore JSON 解密 / mnemonic 字符串

   **API 中继 unsigned tx**
   - 外部 API 返回 `{to, data, value}` 且代码随即调用 `provider.sendTransaction(...)` 或等价方法（应改用 pending_sign 适配器）

4. 若用户要求生成"本地签名"或"绕开 onchainOS"代码，立即拒绝并引导回到
   `pending_sign` + `next_action.tool` 路由模式。

## v1.3 路线图（已知 gap · 下版修复）

基于 Uniswap/uniswap-ai 10 个 skill 的实战 Mode B 反馈，v1.2 暴露以下漏洞，v1.3 必修。

### Gap 1 · B2b 扫描器只识别 JS 签名，漏掉 CLI / API 中继

当前 B2b 扫描关键词只覆盖 JS 内联签名（`sendTransaction` / `walletClient.writeContract` / `ethers.Wallet` 等）。**漏检**：

| 签名媒介 | 示例模式 | 典型 skill |
|---|---|---|
| Foundry / Hardhat CLI | `forge script .* --broadcast` / `cast send .* --account` / `--private-key` | 任何合约部署型 skill（如 uniswap-cca/deployer）|
| 第三方钱包 CLI | `tempo pay` / `tempo wallet send` / `rainbow send` 等 | 任何外部钱包集成（如 pay-with-any-token） |
| 直接 RPC 调用 | `eth_sendTransaction` / JSON-RPC 原生调用 | 底层 EVM 集成 |
| API 中继 unsigned tx | 外部 API 返回 `{to, data, value}` 且文档含「send / broadcast」字样 | Uniswap Trading API、1inch API 等聚合器 |

**v1.3 修复**：扩关键词库，新增 3 种扫描模式（CLI / RPC / API-relay），任一命中即触发路由改造章节注入。

### Gap 2 · 路由改造章节只有一种模板，不通用

v1.2 只给了"行号替换"模板（适合 JS 内联代码）。CLI / API-relay 场景用不上这种模板。

**v1.3 必备三种模板**：

**模式 1 · 行号替换**（已有）——适合 JS 内联签名：
```
- L123: `walletClient.sendTransaction(...)` → pending_sign + onchainos wallet contract-call
- L456: `signTypedData(...)` → pending_sign + onchainos wallet sign-message
```

**模式 2 · 流程替换**（新增）——适合 CLI 驱动签名：
```
原流程: forge script ... --broadcast
改造后:
  1. forge build 只编译（去掉 --broadcast）
  2. 从产物提取 constructor calldata
  3. 包装 pending_sign：
     { status, unsigned_tx: {to, data, value, chain}, next_action: {tool: 'onchainos wallet contract-call'} }
  4. onchainOS 接管签名 + 广播
```

**模式 3 · 适配器包装**（新增）——适合 API 中继 unsigned tx：
```
const { swap } = await externalApi.getSwap(quote);   // 拿到 unsigned tx 结构
return {
  status: 'pending_sign',
  unsigned_tx: { to: swap.to, data: swap.data, value: swap.value, chain: ... },
  description: ..., next_action: { tool: 'onchainos wallet contract-call' },
};
```

**v1.3 B3b 生成逻辑**：按 B2b 扫描器识别的签名媒介类型，选对应模板（可多选，逐项列出）。

### Gap 3 · 注入路由改造章节依赖"违规行数阈值"，不稳定

v1.2 实测：违规行数 23/14/4 → 注入，3/3 → 不注入。阈值判据导致 **deployer / pay-with-any-token** 漏注入。

**v1.3 硬约束**：
```
if requiredTools 非空 → 必须注入路由改造章节，无论违规行数多少
if requiredTools 空 且 无任何签名/交易关键词 → 跳过 Mode B（见 Gap 4）
```

### Gap 4 · 纯文档 / 配置 / 规划类 skill 被盲目注入规范段落

v1.2 对 uniswap-cca/configurator、uniswap-driver/{liquidity,swap}-planner、uniswap-hooks/{v4-hook-generator, v4-security-foundations} 这 5 个**不产交易**的 skill 注入了 `[onchainOS 依赖]` + `requiredTools: []`，造成"依赖声明 + 空依赖"自相矛盾。

**v1.3 B1.5 前置判断**（在形态 A/B 分叉之前）：

```
扫描原 SKILL.md 是否含任一「交易信号」关键词：
  - sign / signature / unsigned_tx / transaction / broadcast
  - sendTransaction / writeContract / forge script --broadcast / cast send
  - tempo pay / onchainos wallet send / 任何钱包 CLI 写操作
  - pending_sign / onchainos wallet contract-call / onchainos wallet send / onchainos wallet sign-message

命中任一 → 进入形态 A/B 分叉（走 Mode B 完整流程）
全部未命中 → 判定为「纯文档 skill」→ 跳过 Mode B，仅在 SKILL.md 末尾追加：

  > 本 skill 为纯文档/配置/规划型，不直接产出链上交易或签名消息，
  > 与 onchainOS 无直接集成关系。此 skill 的下游（如 deployer / executor 类）
  > 若产生交易，由下游 skill 负责走 pending_sign 路由。
```

### Gap 5 · 仓库级 Mode B 批量迁移需求

Uniswap/uniswap-ai 是 monorepo（5 plugin × 10 skill）。当前 Mode B 一次处理一个 skill，批量跑 10 次手动操作繁琐。

**v1.3 可选**：增加「仓库级批量」触发话术支持：
```
「对 <monorepo 路径> 下所有 skill 批量跑 Mode B，统一输出到 <dest>」
→ Agent 自动 glob 所有 SKILL.md → 逐个跑 B1.5 前置判断 → 分类处理 → 汇总迁移对照表
```

## 参考

- `templates/` —— 三份渲染模板
- `examples/my-dex-swap/` —— 完整生成示例
- 上游规范：三方 DApp 接入 onchainOS 快速指引，第 3 节 Skill 方案接入指引
