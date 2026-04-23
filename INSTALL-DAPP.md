# 三方 DApp Skill 一键安装（本地已有 Skill 时使用）

适用对象：你已经有一份自己的 Claude Code Skill（可能是你写的业务 Skill，或别人发的），
现在想把它放进 Claude Code 的 skills 目录，并准备用脚手架做 onchainOS 集成。

## 场景 A · Skill 来自 GitHub

```bash
git clone <dapp-skill-repo>  ~/.claude/skills/<dapp-name>
```

示例：

```bash
git clone https://github.com/my-org/my-dex  ~/.claude/skills/my-dex
```

## 场景 B · Skill 来自本地目录（开发中）

```bash
# 方式 1：软链（改源码即时生效，推荐开发中用）
ln -s "$(pwd)/my-dex"   ~/.claude/skills/my-dex

# 方式 2：硬拷贝（稳定、可分发）
cp -r "$(pwd)/my-dex"   ~/.claude/skills/my-dex
```

## 场景 C · Skill 来自 zip / tar 包

```bash
tar -xzf my-dex.tgz -C ~/.claude/skills/
# 或
unzip my-dex.zip -d ~/.claude/skills/
```

## 安装后自检（3 条命令，10 秒）

```bash
SKILL=~/.claude/skills/<dapp-name>

# 1. SKILL.md 存在且 YAML frontmatter 合法
python3 -c "import yaml; yaml.safe_load(open('$SKILL/SKILL.md').read().split('---',2)[1])" && echo ✓ frontmatter

# 2. 结构合规（至少 SKILL.md，可选 index.ts / README.md）
test -f $SKILL/SKILL.md && echo ✓ structure

# 3. Claude Code 识别到
claude mcp list 2>/dev/null | grep -i "$(basename $SKILL)" || \
  echo "⚠ 若对话里 / 不出现该 Skill 名，重启 Claude Code 或新开会话"
```

## 和脚手架配合：升级为 onchainOS-integrated Skill

三方 DApp Skill 和脚手架都装好后，在 Claude Code 对话里说：

```
我有一个现成的 DApp Skill 在 ~/.claude/skills/<dapp-name>，
帮我按 onchainOS Skill 方案（脚手架的规范）升级它，
输出到 ~/.claude/skills/<dapp-name>-onchainos/
```

Agent 会自动：
1. 读取现有 Skill 的 SKILL.md + index.ts
2. 识别每个工具的业务类型
3. 按脚手架规范加 [onchainOS 依赖] / [签名约束] / requiredTools / Pre-flight Checks
4. 把交易类工具包装成 pending_sign 返回
5. 保留原有业务逻辑作为内部 helper
6. 跑自检 → 报告结果
