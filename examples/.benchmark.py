"""
onchainos-dapp-scaffold benchmark
  - 4 businessTypes x 3 files x 11 assertions
  - in-memory render (no disk I/O needed — sandbox safe)
  - timing
"""
import pathlib, re, time, yaml, sys, json

ROOT = pathlib.Path.home() / '.claude/skills/onchainos-dapp-scaffold'
TPL  = ROOT / 'templates'

# ── businessType matrix ─────────────────────────────────────────────
BIZ = {
    'swap': {
        'next_tool': 'onchainos wallet contract-call',
        'required':  ['onchainos wallet contract-call', 'onchainos gateway broadcast'],
        'example_prompt': 'Swap 100 USDC to ETH on Ethereum',
    },
    'transfer': {
        'next_tool': 'onchainos wallet send',
        'required':  ['onchainos wallet send', 'onchainos gateway broadcast'],
        'example_prompt': 'Send 50 USDC to 0xAbc...',
    },
    'contract-call': {
        'next_tool': 'onchainos wallet contract-call',
        'required':  ['onchainos wallet contract-call', 'onchainos gateway broadcast'],
        'example_prompt': 'Mint NFT token #42',
    },
    'sign-message': {
        'next_tool': 'onchainos wallet sign-message',
        'required':  ['onchainos wallet sign-message'],
        'example_prompt': 'Sign login challenge for app.example.com',
    },
}

REASONS = {
    'onchainos wallet contract-call': 'calldata -> TEE sign -> broadcast',
    'onchainos wallet send':          'native / ERC-20 transfer',
    'onchainos wallet sign-message':  'personalSign / EIP-712 sign',
    'onchainos gateway broadcast':    'broadcast signed tx',
}

# ── render helpers ──────────────────────────────────────────────────
def req_yaml(ts):
    out = []
    for t in ts:
        out += [f'  - name: {t}', '    provider: onchainos',
                '    install: "npx skills add okx/onchainos-skills"',
                f'    reason: "{REASONS[t]}"']
    return '\n'.join(out)

def tools_yaml(ts):
    return '\n'.join(f'  - name: {n}\n    description: "{d}"' for n,d in ts)

def tool_fns(biz, tools, primary_chain, next_tool):
    """Apply SKILL.md generation rules strictly per businessType."""
    bodies = []
    for n,_ in tools:
        if biz == 'sign-message':
            body = (
                f"async function {n}(params: any) {{\n"
                f"  // TODO [三方] 生成待签名消息（personalSign / EIP-712）\n"
                f"  const TODO = (f: string): never => {{ throw new Error(`[SCAFFOLD-UNFILLED] ${{f}}`); }};\n"
                f"  return {{\n"
                f"    status: 'pending_sign',\n"
                f"    message: TODO('message'),\n"
                f"    description: TODO('description'),\n"
                f"    next_action: {{ tool: '{next_tool}' }},\n"
                f"  }};\n"
                f"}}"
            )
        elif biz == 'transfer':
            body = (
                f"async function {n}(params: any): Promise<PendingSign> {{\n"
                f"  // TODO [三方] 解析 to / amount / token\n"
                f"  const TODO = (f: string): never => {{ throw new Error(`[SCAFFOLD-UNFILLED] ${{f}}`); }};\n"
                f"  const unsigned_tx = {{\n"
                f"    to: TODO('to'), data: '0x', value: TODO('value'), chain: '{primary_chain}',\n"
                f"  }};\n"
                f"  return {{\n"
                f"    status: 'pending_sign',\n"
                f"    unsigned_tx,\n"
                f"    description: TODO('description'),\n"
                f"    next_action: {{ tool: '{next_tool}' }},\n"
                f"  }};\n"
                f"}}"
            )
        else:  # swap / contract-call
            body = (
                f"async function {n}(params: any): Promise<PendingSign> {{\n"
                f"  // TODO [三方] 查路由 / 算价 / 构造 calldata\n"
                f"  const TODO = (f: string): never => {{ throw new Error(`[SCAFFOLD-UNFILLED] ${{f}}`); }};\n"
                f"  const unsigned_tx = {{\n"
                f"    to: TODO('to'), data: TODO('data'), value: '0', chain: '{primary_chain}',\n"
                f"  }};\n"
                f"  return {{\n"
                f"    status: 'pending_sign',\n"
                f"    unsigned_tx,\n"
                f"    description: TODO('description'),\n"
                f"    next_action: {{ tool: '{next_tool}' }},\n"
                f"  }};\n"
                f"}}"
            )
        bodies.append(body)
    return '\n\n'.join(bodies) + f"\n\nexport {{ {', '.join(n for n,_ in tools)} }};"

def render_all(biz_name):
    cfg = BIZ[biz_name]
    chains = ['eip155:1', 'eip155:137']
    tools  = [(f'my_{biz_name.replace("-","_")}_tool', f'{biz_name} tool')]
    V = {
        'NAME':                f'bench-{biz_name}',
        'VERSION':             '1.0.0',
        'AUTHOR':              'bench-team',
        'CHAINS':              ', '.join(chains),
        'PRIMARY_CHAIN':       chains[0],
        'DESCRIPTION':         f'Benchmark DApp for businessType={biz_name}',
        'EXAMPLE_USER_PROMPT': cfg['example_prompt'],
        'REQUIRED_TOOLS_YAML': req_yaml(cfg['required']),
        'REQUIRED_TOOL_NAMES': ', '.join(cfg['required']),
        'TOOLS_YAML':          tools_yaml(tools),
        'TOOL_FUNCTIONS':      tool_fns(biz_name, tools, chains[0], cfg['next_tool']),
        'NEXT_ACTION_TOOL':    cfg['next_tool'],
    }
    out = {}
    for src, dst in [('SKILL.md.template','SKILL.md'),
                     ('index.ts.template','index.ts'),
                     ('README.md.template','README.md')]:
        body = (TPL/src).read_text()
        for k,v in V.items():
            body = body.replace('{{'+k+'}}', v)
        out[dst] = body
    return out, V

# ── assertions ──────────────────────────────────────────────────────
def assertions(files, V, biz_name):
    skill, ts, readme = files['SKILL.md'], files['index.ts'], files['README.md']
    cfg = BIZ[biz_name]
    meta = yaml.safe_load(skill.split('---',2)[1])

    # non-comment code lines only
    code_lines = [l for l in ts.splitlines() if not l.lstrip().startswith('//')]
    code = '\n'.join(code_lines)

    return [
        ('R0  无未解析 {{VAR}}（3 份文件）',
            all(not re.search(r'\{\{[A-Z_]+\}\}', f) for f in files.values())),
        ('A1  SKILL.md frontmatter YAML 合法',
            isinstance(meta, dict) and meta['name'] == V['NAME']),
        ('A2  三处 [固定] 段落齐全',
            all(s in skill for s in ['[onchainOS 依赖]', '[签名约束]',
                                     '## Pre-flight Checks', '## Signing Constraint'])),
        ('A3  next_action.tool 与 businessType 匹配',
            f"next_action: {{ tool: '{cfg['next_tool']}' }}" in ts),
        ('A4  requiredTools 与 next_action.tool 对齐',
            all(any(t['name']==r for t in meta['requiredTools']) for r in cfg['required'])),
        ('A5  无本地签名代码（忽略注释）',
            not re.search(r'ethers\.Wallet|signTransaction|sendTransaction|privateKey', code)),
        ('A6  chains 解析正确',
            meta['chains'] == ['eip155:1', 'eip155:137']),
        ('A7  tools 声明与函数定义对齐',
            all(f"function {t['name']}" in ts for t in meta['tools'])),
        ('A8  Pre-flight 明示所有 requiredTools',
            all(r in skill.split('## Pre-flight Checks')[1].split('## Signing')[0]
                for r in cfg['required'])),
        ('A9  export 语句完整',
            'export {' in ts and all(t['name'] in ts.split('export {')[1] for t in meta['tools'])),
        ('A10 README 示例来自 EXAMPLE_USER_PROMPT，非硬编码 swap',
            cfg['example_prompt'] in readme
            and (biz_name == 'swap' or 'swap 100 USDC for ETH' not in readme)),
        ('A11 index.ts 顶部有 RUNTIME MODEL 警告',
            'RUNTIME MODEL' in ts),
    ]

# ── run ────────────────────────────────────────────────────────────
print(f'{"case":20s} │ {"render(ms)":>11s} │ pass/total  │ failures')
print('─'*20 + '─┼─' + '─'*11 + '─┼─' + '─'*11 + '─┼─' + '─'*30)

summary = {}
total_pass, total_all = 0, 0
for biz in BIZ:
    t0 = time.perf_counter_ns()
    files, V = render_all(biz)
    t_render_us = (time.perf_counter_ns() - t0) / 1000
    t_render_ms = t_render_us / 1000

    checks = assertions(files, V, biz)
    passed = sum(1 for _, ok in checks if ok)
    total  = len(checks)
    fails  = [n for n, ok in checks if not ok]

    total_pass += passed
    total_all  += total
    summary[biz] = (passed, total, fails, t_render_ms)

    fail_s = ('; '.join(fails) if fails else '—')[:30]
    print(f'{biz:20s} │ {t_render_ms:11.3f} │ {passed:5d}/{total:<5d} │ {fail_s}')

print('─'*20 + '─┴─' + '─'*11 + '─┴─' + '─'*11 + '─┴─' + '─'*30)
print(f'{"TOTAL":20s}   {"":>11}   {total_pass:5d}/{total_all:<5d}')

pass_rate = total_pass / total_all * 100
print(f'\npass rate: {pass_rate:.1f}%  ({total_pass}/{total_all})')
sys.exit(0 if total_pass == total_all else 1)
