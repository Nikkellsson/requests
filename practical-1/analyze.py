"""Usage: python analyze.py PATH_TO_REQUESTS_CLONE"""
import ast
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from radon.complexity import cc_visit
from radon.raw import analyze

home = Path(__file__).resolve().parent
root = Path(sys.argv[1]).resolve()
files = [Path("src/requests") / (name + ".py") for name in ("models", "sessions", "adapters")]
results = {}
windows = defaultdict(list)
class_ids = {}
for file in files:
    source = (root / file).read_text(encoding="utf-8")
    tree = ast.parse(source)
    raw = analyze(source)
    blocks = []
    for block in cc_visit(source):
        if hasattr(block, "is_method"):
            blocks.append((block.fullname, block.lineno, block.complexity))
    classes = {}
    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imports[name] = ((("." * node.level) + (node.module or "")) if isinstance(node, ast.ImportFrom) else alias.name)
        for _, body in ast.iter_fields(node):
            if not isinstance(body, list) or not body or not all(isinstance(s, ast.stmt) for s in body):
                continue
            for i in range(len(body)-2):
                group = body[i:i+3]
                if any(isinstance(s, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)) or (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) for s in group):
                    continue
                windows[tuple(ast.dump(s) for s in group)].append((file.name, group[0].lineno, group[-1].end_lineno))
    for c in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        names = {n.id for n in ast.walk(c) if isinstance(n, ast.Name)}
        attrs = sorted({n.attr for n in ast.walk(c) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == 'self' and isinstance(n.ctx, ast.Store)})
        methods = [n.name for n in c.body if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
        classes[c.name] = dict(fields=attrs, methods=methods, dependencies=sorted({imports[n] for n in names if n in imports}))
        class_ids[c.name] = names
    results[file.name] = dict(lines=len(source.splitlines()), sloc=raw.sloc, blocks=blocks, classes=classes)
for data in results.values():
    for name, c in data['classes'].items():
        c['incoming'] = sorted(other for other, ids in class_ids.items() if other != name and name in ids)
duplicates = [v for v in windows.values() if len(v)>1]
cmd = ['ruff','check','--config',str(home/'ruff.toml'),'--output-format','json', *map(str,files)]
run = subprocess.run(cmd,cwd=root,capture_output=True,encoding='utf-8')
if run.returncode not in (0,1):
    raise RuntimeError(run.stderr)
issues = json.loads(run.stdout)
# The three input files have unique ASCII names, even under a Unicode directory.
paths_by_name = {file.name: file.as_posix() for file in files}
for issue in issues:
    issue['filename'] = paths_by_name[Path(issue['filename']).name]
(home/'results.json').write_text(json.dumps(dict(files=results,duplicates=duplicates,ruff=issues),indent=2),encoding='utf-8')
