#!/usr/bin/env bash
# OnchainOS DApp Scaffold Skill · One-line installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/BlueBd/test-dapp-skill-scaffolding/main/install.sh | sh
#
# Or local preview (internal):
#   bash install.sh
#
# Installs to: ~/.claude/skills/onchainos-dapp-scaffold/

set -e

SKILL_NAME="onchainos-dapp-scaffold"
DEST="${HOME}/.claude/skills/${SKILL_NAME}"
REPO="${ONCHAINOS_SCAFFOLD_REPO:-https://github.com/BlueBd/test-dapp-skill-scaffolding.git}"

echo "▶ Installing ${SKILL_NAME} to ${DEST}"

# Claude Code check
if ! command -v claude >/dev/null 2>&1; then
  echo "✗ Claude Code 未安装。先装 Claude Code：https://claude.com/claude-code"
  exit 1
fi

mkdir -p "${HOME}/.claude/skills"

if [ -d "${DEST}" ]; then
  echo "⚠ 已存在，更新到最新："
  cd "${DEST}" && git pull --ff-only 2>/dev/null || echo "  （非 git 仓库，跳过 pull）"
else
  git clone --depth 1 "${REPO}" "${DEST}" 2>/dev/null || {
    echo "✗ git clone 失败（可能仓库未公开发布）。请手动：cp -r <预览目录> ${DEST}"
    exit 1
  }
fi

# 自检
test -f "${DEST}/SKILL.md" || { echo "✗ SKILL.md 缺失"; exit 1; }
test -d "${DEST}/templates" || { echo "✗ templates/ 缺失"; exit 1; }

echo "✓ 安装完成：${DEST}"
echo ""
echo "在 Claude Code 对话框说一句即可触发："
echo "  生成 DApp Skill：名字 my-dex-swap，业务 swap"
