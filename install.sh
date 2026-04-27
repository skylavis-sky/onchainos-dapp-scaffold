#!/usr/bin/env bash
# Onchain OS DApp Scaffold Skill · One-line installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/okx/dapp-connect-agenticwallet/main/install.sh | sh
#
# Or local preview (internal):
#   bash install.sh
#
# Installs to: ~/.agents/skills/onchainos-dapp-scaffold/  (universal location;
# Claude Code reads from ~/.claude/skills/ via symlink, OpenClaw / Codex /
# Cursor read from ~/.agents/skills/ directly).

set -euo pipefail

SKILL_NAME="onchainos-dapp-scaffold"
DEST="${HOME}/.agents/skills/${SKILL_NAME}"
CLAUDE_LINK="${HOME}/.claude/skills/${SKILL_NAME}"
REPO="${ONCHAINOS_SCAFFOLD_REPO:-https://github.com/okx/dapp-connect-agenticwallet.git}"

echo "▶ Installing ${SKILL_NAME} to ${DEST}"

# Soft check: warn if no skills-protocol agent CLI is found, but don't exit.
# The scaffold's actual triggers run inside whichever agent the developer
# uses; install just needs to drop files in the right place.
if ! command -v claude >/dev/null 2>&1 \
   && ! command -v codex >/dev/null 2>&1 \
   && ! command -v openclaw >/dev/null 2>&1; then
  echo "⚠ No skills-protocol agent CLI detected (claude / codex / openclaw)."
  echo "  Files will still be installed to ${DEST}; make sure your agent reads from there."
fi

mkdir -p "${HOME}/.agents/skills"
mkdir -p "${HOME}/.claude/skills"

if [ -d "${DEST}" ]; then
  echo "⚠ Already installed; pulling latest:"
  ( cd "${DEST}" && git pull --ff-only 2>/dev/null ) || echo "  (not a git repo, skipping pull)"
else
  if ! git clone --depth 1 "${REPO}" "${DEST}" 2>/dev/null; then
    echo "✗ git clone failed (repo URL may be wrong or unreachable)."
    echo "  Tried: ${REPO}"
    echo "  Fix: set ONCHAINOS_SCAFFOLD_REPO=<url> and re-run."
    exit 1
  fi
fi

# Symlink into Claude Code's skills dir (other agents read ~/.agents/skills/ directly)
ln -sfn "${DEST}" "${CLAUDE_LINK}"

# Self-check
test -f "${DEST}/SKILL.md" || { echo "✗ SKILL.md missing"; exit 1; }
test -d "${DEST}/templates" || { echo "✗ templates/ missing"; exit 1; }

echo "✓ Installed: ${DEST}"
echo "  Symlinked → ${CLAUDE_LINK}"
echo ""
echo "Restart your AI agent, then trigger the scaffold by saying:"
echo "  Use the scaffold to upgrade ~/.agents/skills/your-existing-skill"
echo ""
echo "(Claude Code users can also use ~/.claude/skills/your-existing-skill — the symlink is equivalent.)"

# TODO: once scaffold is published as an OKX skills-protocol package,
# replace the git-clone path with:
#   npx skills add okx/onchainos-dapp-scaffold --yes --global
# That'll handle multi-agent symlinking automatically.
