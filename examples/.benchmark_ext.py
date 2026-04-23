"""Extended benchmark: multi-tool stress + negative test + timing stats (P50/P95/P99)."""
import pathlib, re, time, yaml, sys, statistics

ROOT = pathlib.Path.home() / '.claude/skills/onchainos-dapp-scaffold'
TPL  = ROOT / 'templates'

REASONS = {
    'onchainos wallet contract-call': 'calldata -> TEE sign -> broadcast',
    'onchainos wallet send':          'native / ERC-20 transfer',
    'onchainos wallet sign-message':  'personalSign / EIP-712 sign',
    'onchainos gateway broadcast':    'broadcast signed tx',
}

def req_yaml(ts):
    out = []
    for t in ts:
        out += [f'  - name: {t}', '    provider: onchainos',
                '    install: "npx skills add okx/onchainos-skills"',
                f'    reason: "{REASONS[t]}"']
    return '\n'.join(out)

def tools_yaml(ts):
    return '\n'.join(f'  - name: {n}\n    description: "{d}"' for n,d in ts)

def fn_skeleton(biz, name, chain, next_tool):
    """v1.2: throw-style TODO placeholders."""
    throw_helper = "  const TODO = (f: string): never => { throw new Error(`[SCAFFOLD-UNFILLED] ${f}`); };\n"
    if biz == 'sign-message':
        return (f"async function {name}(params: any) {{\n"
                f"  // TODO [三方] 生成待签名消息\n"
                + throw_helper +
                f"  return {{\n"
                f"    status: 'pending_sign',\n"
                f"    message: TODO('message'),\n"
                f"    description: TODO('description'),\n"
                f"    next_action: {{ tool: '{next_tool}' }},\n"
                f"  }};\n"
                f"}}")
    todo = ('解析 to/amount/token' if biz=='transfer' else '查路由/算价/构造 calldata')
    data = "'0x'" if biz=='transfer' else "TODO('data')"
    value = "TODO('value')" if biz=='transfer' else "'0'"
    return (f"async function {name}(params: any): Promise<PendingSign> {{\n"
            f"  // TODO [三方] {todo}\n"
            + throw_helper +
            f"  const unsigned_tx = {{\n"
            f"    to: TODO('to'), data: {data}, value: {value}, chain: '{chain}',\n"
            f"  }};\n"
            f"  return {{\n"
            f"    status: 'pending_sign',\n"
            f"    unsigned_tx,\n"
            f"    description: TODO('description'),\n"
            f"    next_action: {{ tool: '{next_tool}' }},\n"
            f"  }};\n"
            f"}}")

def tool_fns(biz, tools, chain, next_tool):
    return '\n\n'.join(fn_skeleton(biz, n, chain, next_tool) for n,_ in tools) \
           + f"\n\nexport {{ {', '.join(n for n,_ in tools)} }};"

def render(biz, chains, tools, next_tool, req_tools, example_prompt):
    V = {
        'NAME': f'bench-{biz}', 'VERSION': '1.0.0', 'AUTHOR': 'bench',
        'CHAINS': ', '.join(chains), 'PRIMARY_CHAIN': chains[0],
        'DESCRIPTION': f'Benchmark {biz}',
        'EXAMPLE_USER_PROMPT': example_prompt,
        'REQUIRED_TOOLS_YAML': req_yaml(req_tools),
        'REQUIRED_TOOL_NAMES': ', '.join(req_tools),
        'TOOLS_YAML': tools_yaml(tools),
        'TOOL_FUNCTIONS': tool_fns(biz, tools, chains[0], next_tool),
        'NEXT_ACTION_TOOL': next_tool,
    }
    out = {}
    for src, dst in [('SKILL.md.template','SKILL.md'),
                     ('index.ts.template','index.ts'),
                     ('README.md.template','README.md')]:
        body = (TPL/src).read_text()
        for k,v in V.items():
            body = body.replace('{{'+k+'}}', v)
        out[dst] = body
    return out

# ═══════ Test 1: multi-tool stress (3 tools in one skill) ═══════
print('╔═══ Test 1: multi-tool stress (3 tools pipeline) ═══╗')
tools_3 = [
    ('my_search_token', '查询 token 元数据（只读）'),
    ('my_get_price',    '查询路由与报价（只读）'),
    ('my_build_swap',   '构造 swap unsigned_tx'),
]
files = render('swap', ['eip155:1'], tools_3, 'onchainos wallet contract-call',
               ['onchainos wallet contract-call', 'onchainos gateway broadcast'],
               'swap 100 USDC for ETH')
ts = files['index.ts']

checks_t1 = [
    ('3 个函数定义齐全',
        all(f'function {n}' in ts for n,_ in tools_3)),
    ('export 声明含所有 3 个工具',
        all(n in ts.split('export {')[1].split('}')[0] for n,_ in tools_3)),
    ('每个函数独立 pending_sign 外壳（1 type + 3 fn = 4 hits）',
        ts.count("status: 'pending_sign'") == 4),
    ('每个函数独立 next_action 路由（1 type + 3 fn = 4 hits）',
        ts.count("next_action: { tool:") == 4),
    ('SKILL.md tools 数组 3 项',
        len(yaml.safe_load(files['SKILL.md'].split('---',2)[1])['tools']) == 3),
    ('requiredTools 保持 2 项（不随工具数膨胀）',
        len(yaml.safe_load(files['SKILL.md'].split('---',2)[1])['requiredTools']) == 2),
]
for n, ok in checks_t1: print(f'  {"PASS" if ok else "FAIL"}  {n}')
t1_pass = sum(1 for _,ok in checks_t1 if ok)
print(f'  → {t1_pass}/{len(checks_t1)}\n')

# ═══════ Test 2: negative tests — inject errors, verify assertions catch ═══════
print('╔═══ Test 2: negative test (inject mismatches) ═══╗')

neg_cases = [
    # (name, mutator, expected-to-fail-check)
    ('mismatch: next_action.tool ≠ requiredTools',
        lambda f: {**f, 'index.ts': f['index.ts'].replace(
            "next_action: { tool: 'onchainos wallet contract-call' }",
            "next_action: { tool: 'onchainos wallet send' }")},
        'A3 next_action.tool 匹配'),
    ('corruption: 删除 [签名约束] 段',
        lambda f: {**f, 'SKILL.md': f['SKILL.md'].replace('[签名约束]', '[已删除]')},
        'A2 三处 [固定] 段落齐全'),
    ('injection: index.ts 出现 ethers.Wallet',
        lambda f: {**f, 'index.ts':
            f['index.ts'].replace(
                "export {",
                "const w = new ethers.Wallet(pk); pk.signTransaction(tx);\nexport {")},
        'A5 无本地签名代码'),
]

base = render('swap', ['eip155:1'], [('my_build_swap','swap tool')],
              'onchainos wallet contract-call', ['onchainos wallet contract-call','onchainos gateway broadcast'],
              'swap test')

for name, mut, expected_fail in neg_cases:
    mutated = mut(base)
    skill, ts_ = mutated['SKILL.md'], mutated['index.ts']
    meta = yaml.safe_load(skill.split('---',2)[1]) if '---' in skill else {}
    code = '\n'.join(l for l in ts_.splitlines() if not l.lstrip().startswith('//'))

    a3_ok = "next_action: { tool: 'onchainos wallet contract-call' }" in ts_
    a2_ok = all(s in skill for s in ['[onchainOS 依赖]','[签名约束]',
                                     '## Pre-flight Checks','## Signing Constraint'])
    a5_ok = not re.search(r'ethers\.Wallet|signTransaction|sendTransaction|privateKey', code)
    detected = (not a3_ok) or (not a2_ok) or (not a5_ok)
    print(f'  {"DETECTED" if detected else "MISSED  "}  {name}  (expected: {expected_fail})')

# ═══════ Test 3: timing distribution (100 renders) ═══════
print('\n╔═══ Test 3: timing distribution (N=100) ═══╗')
times = []
for _ in range(100):
    t0 = time.perf_counter_ns()
    render('swap', ['eip155:1','eip155:137'],
           [('my_build_swap','swap')],
           'onchainos wallet contract-call',
           ['onchainos wallet contract-call','onchainos gateway broadcast'],
           'swap 100 USDC')
    times.append((time.perf_counter_ns() - t0) / 1000)  # µs

q = statistics.quantiles(times, n=100)
print(f'  N=100 renders')
print(f'    min:    {min(times):8.1f} µs')
print(f'    P50:    {q[49]:8.1f} µs')
print(f'    P95:    {q[94]:8.1f} µs')
print(f'    P99:    {q[98]:8.1f} µs')
print(f'    max:    {max(times):8.1f} µs')
print(f'    mean:   {statistics.mean(times):8.1f} µs')
print(f'    stdev:  {statistics.stdev(times):8.1f} µs')
