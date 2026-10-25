from pathlib import Path
import re

ROOT=Path('/runtime')
MODELS=ROOT/'backend/app/models.py'
MAIN=ROOT/'backend/app/main.py'

models=MODELS.read_text()
main=MAIN.read_text()

for cls in ('User','Lead'):
    m=re.search(rf'class\s+{cls}\b.*?(?=\nclass\s+|\Z)', models, re.S)
    print(f'--- AUTHZ PROBE {cls} ---')
    print((m.group(0)[:5000] if m else 'NOT FOUND'))

for pattern in (r"@app\.get\('/api/leads'\).*?(?=\n@app\.|\Z)", r"@app\.get\('/api/leads/\{.*?(?=\n@app\.|\Z)", r"@app\.post\('/api/leads'\).*?(?=\n@app\.|\Z)", r"def\s+current_user.*?(?=\ndef\s+|\n@app\.|\Z)"):
    m=re.search(pattern, main, re.S)
    print('--- AUTHZ PROBE ROUTE ---')
    print((m.group(0)[:8000] if m else 'NOT FOUND'))
