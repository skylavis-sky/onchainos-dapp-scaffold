# 🎯 概览

当前支持 3 个三方 DApp 测试端点。不同 DApp 对应不同 businessType，覆盖脚手架 Mode B 的多条生成路径。

- Uniswap · businessType=swap · DEX 换币 · 简单
- GMX · businessType=contract-call · 永续合约 / LP · 中等复杂度
- Morpho · businessType=contract-call · 借贷 / 存款 · 中等 · ⚠ pre-v1.0 实验性

❌ 不支持：1inch（是 MCP 指针 skill，不是独立 Claude skill）。详见附录 A。

## ⚙ 使用说明

1. 步骤 0 设置 DAPP_CHOICE（三选一）
2. 依次粘贴后续代码块到同一个终端会话
3. 保持终端窗口不关闭 · 所有代码块共享 shell 环境变量
4. 中间有一次重启 Claude Code（已标注 ⏸）

## 🚀 步骤 0 · 选择 DApp 测试端点

```bash
# 📌 三选一，改这一行
export DAPP_CHOICE=uniswap

# 下面 case 自动按选择设置其他变量
case "$DAPP_CHOICE" in
  uniswap)
    export DAPP_REPO_URL=https://github.com/Uniswap/uniswap-ai
    export DAPP_NAME=my-uniswap-swap
    export SKILL_SUBDIR=packages/plugins/uniswap-trading/skills/swap-integration
    export BUSINESS_TYPE=swap
    ;;
  gmx)
    export DAPP_REPO_URL=https://github.com/gmx-io/gmx-ai
    export DAPP_NAME=my-gmx-trading
    export SKILL_SUBDIR=skills/gmx-trading
    export BUSINESS_TYPE=contract-call
    ;;
  morpho)
    export DAPP_REPO_URL=https://github.com/morpho-org/morpho-skills
    export DAPP_NAME=my-morpho-cli
    export SKILL_SUBDIR=skills/morpho-cli
    export BUSINESS_TYPE=contract-call
    echo "⚠ Morpho 仓库是 pre-v1.0 实验性，API 可能变动"
    ;;
  *)
    echo "❌ DAPP_CHOICE 必须是 uniswap / gmx / morpho"
    ;;
esac

# 自检：打印当前配置
echo "DAPP_CHOICE=$DAPP_CHOICE"
echo "DAPP_REPO_URL=$DAPP_REPO_URL"
echo "DAPP_NAME=$DAPP_NAME"
echo "SKILL_SUBDIR=$SKILL_SUBDIR"
echo "BUSINESS_TYPE=$BUSINESS_TYPE"
```

## 🧹 重置测试环境（反复测试前跑一遍）

```bash
# 1. 移除脚手架
rm -rf ~/.claude/skills/onchainos-dapp-scaffold

# 2. 移除当前 DApp 的 skill（升级前 + 升级后两种命名）
rm -rf ~/.claude/skills/"$DAPP_NAME"
rm -rf ~/.claude/skills/"${DAPP_NAME}-onchainos"

# 3. 清理所有 DApp 的克隆临时目录
rm -rf /tmp/uniswap-monorepo /tmp/gmx-monorepo /tmp/morpho-monorepo

# 4. 卸载 onchainOS CLI
rm -rf ~/.local/bin/onchainos
rm -rf ~/.onchainos

# 5. 清 shell 环境变量（保留 DAPP_* 以便复用）
unset ONCHAINOS_TOKEN
unset ONCHAINOS_SCAFFOLD_REPO

# 6. 自检
which onchainos
# 预期输出: onchainos not found

ls ~/.claude/skills/ | grep -E "^(onchainos-dapp-scaffold|${DAPP_NAME})"
# 预期输出: 空行

# ⚠ 清理 skill 目录后必须重启 Claude Code，否则旧注册表仍在
```

## 📦 Part 1 · 从 GitHub 克隆脚手架

脚手架 GitHub 仓库：https://github.com/skylavis-sky/onchainos-dapp-scaffold （MIT、公开）。无需下载附件，直接 git clone 即可。

```bash
# 克隆脚手架到 Claude Code 的 skills 目录
git clone https://github.com/skylavis-sky/onchainos-dapp-scaffold ~/.claude/skills/onchainos-dapp-scaffold

# 自检：确认 SKILL.md 存在
ls ~/.claude/skills/onchainos-dapp-scaffold/SKILL.md
# 预期输出: SKILL.md 路径

# 可选：查看脚手架版本
grep "^version:" ~/.claude/skills/onchainos-dapp-scaffold/SKILL.md
```

## 📥 Part 1 · 克隆 + 复制 DApp skill

```bash
# 1. 克隆到临时目录
TMP_DIR=/tmp/"$DAPP_CHOICE"-monorepo
rm -rf "$TMP_DIR"
git clone "$DAPP_REPO_URL" "$TMP_DIR"

# 2. 复制目标 skill 子目录
cp -r "$TMP_DIR"/"$SKILL_SUBDIR" ~/.claude/skills/"$DAPP_NAME"

# 3. 安全步骤：改写内部 SKILL.md 的 frontmatter name，避免与已装同名 skill 冲突
sed -i.bak "s/^name: .*/name: $DAPP_NAME/" ~/.claude/skills/"$DAPP_NAME"/SKILL.md
rm ~/.claude/skills/"$DAPP_NAME"/SKILL.md.bak

# 4. 验证目录结构
ls ~/.claude/skills/"$DAPP_NAME"/SKILL.md

# 5. 验证 frontmatter name 已改写
grep "^name:" ~/.claude/skills/"$DAPP_NAME"/SKILL.md
# 预期输出: name: [DAPP_NAME 的值]
```

## ⏸ Part 1 → Part 2 · 重启 Claude Code

安装完脚手架和 DApp skill 后 Claude Code 必须重启，新 skill 才能被注册表发现。重启后执行下面命令自动触发 Mode B 升级。

```bash
# 重启 Claude Code 后执行（headless 一键式）
claude -p "用 onchainos-dapp-scaffold 升级 DApp Skill：路径 ~/.claude/skills/$DAPP_NAME，业务类型 $BUSINESS_TYPE"

# 或者重启后打开对话框，把下面这句变量替换成实际值后粘贴：
# 用 onchainos-dapp-scaffold 升级 DApp Skill：路径 ~/.claude/skills/my-uniswap-swap，业务类型 swap
```

## ✅ Part 2 · 验证升级结果

```bash
# 确定性检查：升级后的 skill 应存在
ls ~/.claude/skills/"${DAPP_NAME}-onchainos"/SKILL.md
# 预期输出: SKILL.md 路径

# 查看 frontmatter 确认规范化
grep -A3 "^name:" ~/.claude/skills/"${DAPP_NAME}-onchainos"/SKILL.md | head -10

# 可选：让 Claude 列出新 skill
# claude
# 然后问: 列出我本地名字以 $DAPP_NAME 开头的 skills
```

## 🧪 Part 2 · 按 businessType 执行测试

根据你选的 DAPP_CHOICE，从下面对应章节复制测试 prompt 运行。每个 DApp 给 3 条典型场景。

### Uniswap · businessType=swap

```bash
claude -p "用 my-uniswap-swap-onchainos 把 100 USDC 换成 ETH，链 Ethereum，滑点 0.5%"

claude -p "用 my-uniswap-swap-onchainos 查 1 ETH 能换多少 USDC，链 Ethereum，只报价不广播"

claude -p "用 my-uniswap-swap-onchainos 在 Base 上把 0.01 WETH 换成 USDC"
```

### GMX · businessType=contract-call · 永续合约

```bash
claude -p "用 my-gmx-trading-onchainos 在 Arbitrum 开 ETH 多头 5x 杠杆，仓位 100 USDC，链 Arbitrum"

claude -p "用 my-gmx-trading-onchainos 在 Arbitrum 查 BTC 永续当前资金费率和标记价"

claude -p "用 my-gmx-trading-onchainos 为现有 ETH 多头仓位设置止损价 2500"
```

### Morpho · businessType=contract-call · 借贷

```bash
claude -p "用 my-morpho-cli-onchainos 在 Base 上把 1000 USDC 存入 Morpho Blue 最高 APY 池"

claude -p "用 my-morpho-cli-onchainos 查我在 Ethereum 上的 Morpho 仓位和当前健康因子"

claude -p "用 my-morpho-cli-onchainos 在 Base 上借 500 USDC 用 ETH 作抵押，目标 LTV 50%"
```

预期行为：升级后的 skill 返回 pending_sign 交易对象（含 unsigned_tx + next_action.tool 指向 onchainos wallet contract-call），下一步由 onchainOS CLI 接管签名 + 广播。

## 📎 附录 A · 为什么 1inch 不走这个流程

1inch 的 1inch/1inch-ai 仓库里 skills/1inch-mcp-server/SKILL.md 是一个 MCP 指针 skill，指向 https://api.1inch.com/mcp/protocol 远程服务。它没有本地 TS index.ts 可升级，需要 1inch Business Portal API key，所有签名逻辑在远程服务器。脚手架 Mode B 的升级目标是含 pending_sign 函数的本地 skill，架构不匹配。建议直接当 MCP server 使用，不走脚手架流程。

## 📎 附录 B · 各 DApp 的差异说明

Uniswap: 标准 monorepo 结构，skill 在 packages/plugins/[plugin]/skills/[name]/。直接 cp 即可，scaffold Form A 升级路径，businessType=swap 最常见。

GMX: 平层 skills/[name]/ 结构，subdir 比 Uniswap 浅 2 级。businessType=contract-call 触发 Mode B Form B 存根生成。

Morpho: 同 GMX 平层结构，但仓库 pre-v1.0 实验性状态，schema 可能漂移。生产测试建议 pin commit SHA：在 git clone 后加 cd "$TMP_DIR"; git checkout [commit-sha]。skills/morpho-cli 和 skills/morpho-builder 都在，前者是业务 skill（测试目标选前者），后者是代码生成 meta skill。

## 📎 附录 C · 脚手架更新

脚手架仓库是 MIT 公开仓库，后续版本更新无需重新下载 zip，直接 cd 到 skill 目录 git pull 即可：

```bash
cd ~/.claude/skills/onchainos-dapp-scaffold
git pull origin main

# 查看最新版本号
grep "^version:" SKILL.md
```

## 📋 失败反馈模板

测试中遇到问题，按下面格式反馈（粘到 Lark 评论 / 群）：

```
DAPP_CHOICE=[你选了哪个]
卡在哪个 H2 章节=
完整报错信息=
系统=macOS XX / Linux XX
Claude Code 版本=$(claude --version)
Node 版本=$(node --version)
Git 版本=$(git --version)
脚手架版本=$(grep '^version:' ~/.claude/skills/onchainos-dapp-scaffold/SKILL.md)
```
