import json

with open('coverage.json') as f:
    data = json.load(f)

rows = []
skip = ['migration', '__init__', 'admin.py', 'apps.py', 'tests', 'management']
for fname, info in data['files'].items():
    if any(x in fname for x in skip):
        continue
    pct = info['summary']['percent_covered']
    miss = info['summary']['missing_lines']
    parts = fname.replace('\\', '/').split('apps/')
    name = parts[-1] if len(parts) > 1 else fname
    rows.append((pct, miss, name))

rows.sort()
total_stmts = data['totals']['num_statements']
total_covered = data['totals']['covered_lines']
total_pct = data['totals']['percent_covered']

print("MODULE                                              COV%   MISS")
print("-" * 65)
for pct, miss, name in rows:
    filled = int(pct / 10)
    bar = "#" * filled + "." * (10 - filled)
    flag = " <<<" if pct == 0 else ""
    print(f"{name:<50} {pct:>4.0f}%  {miss:>4}  [{bar}]{flag}")

print()
print(f"TOTAL: {total_pct:.1f}%  ({total_covered}/{total_stmts} lines)")
