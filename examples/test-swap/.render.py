"""Simulate scaffold workflow for swap business type."""
import pathlib, re

ROOT   = pathlib.Path.home() / '.claude/skills/onchainos-dapp-scaffold'
OUTDIR = ROOT / 'examples/test-swap'

inputs = {
    'name': 'test-swap', 'version': '1.0.0', 'author': 'qa-team',
    'chains': ['eip155:1', 'eip155:137'], 'businessType': 'swap',
    'tools': [('my_build_swap', 'build swap unsigned_tx, return pending_sign')],
    'description': 'Test Swap DApp -- scaffold validation.',
}
BIZ = {
    'swap': ('onchainos wallet contract-call', ['onchainos wallet contract-call', 'onchainos gateway broadcast']),
    'transfer': ('onchainos wallet send', ['onchainos wallet send', 'onchainos gateway broadcast']),
    'sign-message': ('onchainos wallet sign-message', ['onchainos wallet sign-message']),
}
REASONS = {
    'onchainos wallet contract-call': 'calldata -> TEE sign -> broadcast',
    'onchainos wallet send': 'native / ERC-20 transfer',
    'onchainos wallet sign-message': 'personalSign / EIP-712 sign',
    'onchainos gateway broadcast': 'broadcast signed tx',
}
next_tool, req = BIZ[inputs['businessType']]

def req_yaml(ts):
    out = []
    for t in ts:
        out += [f'  - name: {t}', '    provider: onchainos',
                '    install: "npx skills add okx/onchainos-skills"',
                f'    reason: "{REASONS[t]}"']
    return '\n'.join(out)

def tools_yaml(ts):
    return '\n'.join(f'  - name: {n}\n    description: "{d}"' for n,d in ts)

def tool_fns(ts, nt):
    bodies = []
    for n,_ in ts:
        bodies.append(
            f"async function {n}(params: any): Promise<PendingSign> {{\n"
            f"  // TODO [third-party] business logic here\n"
            f"  const unsigned_tx = {{ to: '0xTODO', data: '0xTODO', value: '0', chain: 'eip155:1' }};\n"
            f"  return {{\n"
            f"    status: 'pending_sign',\n"
            f"    unsigned_tx,\n"
            f"    description: 'TODO [third-party] human-readable summary',\n"
            f"    next_action: {{ tool: '{nt}' }},\n"
            f"  }};\n"
            f"}}")
    return '\n\n'.join(bodies) + f"\n\nexport {{ {', '.join(n for n,_ in ts)} }};"

V = {
    'NAME': inputs['name'], 'VERSION': inputs['version'], 'AUTHOR': inputs['author'],
    'CHAINS': ', '.join(inputs['chains']), 'DESCRIPTION': inputs['description'],
    'REQUIRED_TOOLS_YAML': req_yaml(req),
    'REQUIRED_TOOL_NAMES': ', '.join(req),
    'TOOLS_YAML': tools_yaml(inputs['tools']),
    'TOOL_FUNCTIONS': tool_fns(inputs['tools'], next_tool),
    'NEXT_ACTION_TOOL': next_tool,
}

for src, dst in [('templates/SKILL.md.template','SKILL.md'),
                 ('templates/index.ts.template','index.ts'),
                 ('templates/README.md.template','README.md')]:
    body = (ROOT/src).read_text()
    for k,v in V.items():
        body = body.replace('{{'+k+'}}', v)
    unresolved = re.findall(r'\{\{[A-Z_]+\}\}', body)
    (OUTDIR/dst).write_text(body)
    print(f'wrote {dst:12s} unresolved={unresolved}')

print('\n--- DIR ---')
for f in sorted(OUTDIR.iterdir()):
    print(f'  {f.name}  {f.stat().st_size} bytes')
