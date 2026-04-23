"""
v1.3 命名空间根治迁移 · 把抽象 tool-registry 名换成真实 CLI 命令

映射表（与 github.com/okx/onchainos-skills v2.3.0 官方 CLI 对齐）：
  wallet_contract_call  →  onchainos wallet contract-call
  wallet_send           →  onchainos wallet send
  wallet_sign_message   →  onchainos wallet sign-message
  gateway_broadcast     →  onchainos gateway broadcast
  onchainos tool list   →  onchainos --version（真实可用检查命令）

处理范围：~/.claude/skills/onchainos-dapp-scaffold/ 下所有 .md / .ts / .py / .template 文件。
"""
import pathlib, re

ROOT = pathlib.Path.home() / '.claude/skills/onchainos-dapp-scaffold'

# 替换顺序：长字符串先，避免 'wallet_send' 错配 'wallet_sign_message' 之类
RENAMES = [
    ('wallet_contract_call', 'onchainos wallet contract-call'),
    ('wallet_sign_message',  'onchainos wallet sign-message'),
    ('gateway_broadcast',    'onchainos gateway broadcast'),
    ('wallet_send',          'onchainos wallet send'),
    # Pre-flight 伪命令 → 真命令
    ('onchainos tool list', 'onchainos --version  # 真实验证 CLI 已装；子命令可用性通过 onchainos wallet --help 和 onchainos gateway --help 查'),
]

TARGETS = [
    '*.md', '*.ts', '*.py', '*.template',
]

def walk_files():
    for pattern in TARGETS:
        for f in ROOT.rglob(pattern):
            # 跳过本脚本自身
            if f.name == '.migrate_v13_naming.py':
                continue
            yield f

changed_files = []
for f in walk_files():
    try:
        text = f.read_text()
    except Exception as e:
        print(f'  skip (read err) {f}: {e}')
        continue
    original = text
    for old, new in RENAMES:
        text = text.replace(old, new)
    if text != original:
        f.write_text(text)
        n = sum(original.count(old) for old, _ in RENAMES)
        changed_files.append((f.relative_to(ROOT), n))

print(f'\n已改写 {len(changed_files)} 个文件：')
for f, n in changed_files:
    print(f'  {n:2d}× {f}')
print(f'\n映射：')
for old, new in RENAMES:
    print(f'  {old!r} → {new!r}')
