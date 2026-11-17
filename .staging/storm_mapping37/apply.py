"""Install NOAA storm report improvements after the existing runtime patches."""
from pathlib import Path
import shutil

ROOT = Path('/runtime')
HERE = Path(__file__).resolve().parent
shutil.copyfile(HERE / 'spc_reports.py', ROOT / 'backend/app/spc_reports.py')
noaa = ROOT / 'backend/app/noaa.py'
source = noaa.read_text()
boundary = '# --- Build 1.0: official MRMS MESH ingestion/cache boundary ---'
assert source.count(boundary) == 1, 'NOAA runtime boundary missing'
noaa.write_text('import httpx\nfrom .spc_reports import fetch_spc_reports\n\n' + boundary + source.split(boundary, 1)[1])
page = ROOT / 'web/map.html'
html = page.read_text()
start = html.index("document.getElementById('noaa').onclick=")
end = html.index("document.getElementById('mrms').onclick=", start)
html = html[:start] + html[end:]
assert html.count('>NOAA Hail</button>') == 1
html = html.replace('>NOAA Hail</button>', '>NOAA Storms</button>')
assert html.count('</body>') == 1
html = html.replace('</body>', '<script src="/assets/storm-mapping.js"></script></body>')
page.write_text(html)
shutil.copyfile(HERE / 'storm-mapping.js', ROOT / 'web/storm-mapping.js')
print('storm_mapping37: NOAA date/type controls and validated SPC reports installed')
