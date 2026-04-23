import pathlib, re, yaml, sys
d = pathlib.Path(__file__).parent
skill  = (d/'SKILL.md').read_text()
ts     = (d/'index.ts').read_text()
readme = (d/'README.md').read_text()

meta = yaml.safe_load(skill.split('---',2)[1])

checks = [
  ('A1  SKILL.md frontmatter YAML 合法',
      isinstance(meta, dict) and meta.get('name') == 'test-swap'),
  ('A2  三处 [固定] 段落齐全',
      all(s in skill for s in ['[onchainOS 依赖]', '[签名约束]',
                               '## Pre-flight Checks', '## Signing Constraint'])),
  ('A3  next_action.tool = onchainos wallet contract-call',
      "next_action: { tool: 'onchainos wallet contract-call' }" in ts),
  ('A4  requiredTools 与 next_action.tool 对齐',
      any(t.get('name') == 'onchainos wallet contract-call' for t in meta['requiredTools'])
      and any(t.get('name') == 'onchainos gateway broadcast'   for t in meta['requiredTools'])),
  ('A5  无本地签名代码（忽略注释行）',
      not any(re.search(r'ethers\.Wallet|signTransaction|sendTransaction|privateKey', line)
              for line in ts.splitlines()
              if not line.lstrip().startswith('//'))),
  ('A6  三文件齐备',
      all((d/f).exists() for f in ['SKILL.md', 'index.ts', 'README.md'])),
  ('A7  chains 正确解析',
      meta['chains'] == ['eip155:1', 'eip155:137']),
  ('A8  tools 声明含 my_build_swap',
      any(t.get('name') == 'my_build_swap' for t in meta['tools'])
      and 'function my_build_swap' in ts),
  ('A9  Pre-flight 明示两个 requiredTools',
      'onchainos wallet contract-call' in skill.split('## Pre-flight Checks')[1]
      and 'onchainos gateway broadcast' in skill.split('## Pre-flight Checks')[1]),
  ('A10 index.ts 可被 TypeScript parse（粗略：有 export）',
      'export { my_build_swap }' in ts),
]

fails = 0
for name, ok in checks:
    print(('PASS' if ok else 'FAIL'), name)
    if not ok: fails += 1
print(f'\n{len(checks)-fails}/{len(checks)} passed')
sys.exit(0 if fails == 0 else 1)
