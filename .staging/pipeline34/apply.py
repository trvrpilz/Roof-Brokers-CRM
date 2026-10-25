from pathlib import Path
import re

ROOT = Path('/runtime')
INDEX = ROOT / 'web/index.html'
MAIN = ROOT / 'backend/app/main.py'

STAGES = ['Lead', 'Prospect', 'Approved', 'Completed', 'Invoiced']
JS_LIST = "['Lead','Prospect','Approved','Completed','Invoiced']"
PY_LIST = '["Lead", "Prospect", "Approved", "Completed", "Invoiced"]'

idx = INDEX.read_text()
idx, js_count = re.subn(
    r"(const\s+PIPELINE\s*=\s*)\[[^\]]*\]",
    lambda m: m.group(1) + JS_LIST,
    idx,
    count=1,
)
if js_count != 1:
    raise SystemExit(f'Pipeline 3.4 patch mismatch: expected one web PIPELINE constant, found {js_count}')
INDEX.write_text(idx)

main = MAIN.read_text()
patched_names = []
for name in ('PIPELINE', 'PIPELINE_STAGES', 'LEAD_STATUSES', 'ALLOWED_LEAD_STATUSES', 'VALID_LEAD_STATUSES'):
    pattern = rf"(^\s*{name}\s*=\s*)(\[[^\]]*\]|\([^\)]*\)|\{{[^\}}]*\}})"
    main, count = re.subn(pattern, lambda m: m.group(1) + PY_LIST, main, count=1, flags=re.MULTILINE)
    if count:
        patched_names.append(name)
MAIN.write_text(main)

print('pipeline34: web stages set to', STAGES)
print('pipeline34: backend constants patched:', patched_names or 'none found')
