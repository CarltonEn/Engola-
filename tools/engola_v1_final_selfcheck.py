from pathlib import Path
import ast, sys

def find_root():
    here=Path(__file__).resolve()
    candidates=[Path.cwd(), *Path.cwd().parents, here.parents[2], *here.parents]
    seen=set()
    for c in candidates:
        c=c.resolve()
        if c in seen: continue
        seen.add(c)
        if (c/'.git').exists() and (c/'main.py').exists(): return c
    return None

ROOT=find_root()
if ROOT is None:
    print('SELFCHECK FAILED: Engola Git repository not found.'); sys.exit(2)
required=['main.py','core/config.py','core/agent.py','core/integration_clients.py',
          'routers/executive.py','routers/integration_actions.py','routers/research.py',
          'static/engola-v1.1.js']
missing=[x for x in required if not (ROOT/x).exists()]
if missing: print('MISSING:',missing); sys.exit(1)
for rel in required:
    if rel.endswith('.py'):
        try: ast.parse((ROOT/rel).read_text(encoding='utf-8'),filename=rel)
        except Exception as e: print('SYNTAX',rel,e); sys.exit(1)
print('ENGOLA 1.0.4 STRUCTURAL SELFCHECK OK')
print('ROOT:',ROOT)
