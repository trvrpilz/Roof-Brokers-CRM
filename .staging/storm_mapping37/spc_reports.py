"""NOAA SPC preliminary reports, independent of radar and contractor evidence."""
import csv
import io
import math
import re
import threading
from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from time import monotonic

import httpx

SPC_BASE = 'https://www.spc.noaa.gov/climo/reports'
KINDS = {'hail': ('hail', 'Size'), 'wind': ('wind', 'Speed'), 'tornado': ('torn', 'F_Scale')}
_cache = {}
_lock = threading.Lock()
TTL_SECONDS = 300


def current_report_day(now=None):
    now = now or datetime.now(timezone.utc)
    return (now - timedelta(hours=12)).date()


def _url_for(day, kind='hail'):
    if kind not in KINDS:
        raise ValueError('kind must be hail, wind, or tornado')
    if not date(1999, 6, 1) <= day <= current_report_day():
        raise ValueError('Select an SPC storm day from June 1, 1999 through the current storm day')
    return f"{SPC_BASE}/{day.strftime('%y%m%d')}_rpts_{KINDS[kind][0]}.csv"


def parse_spc_csv(text, day, kind):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    magnitude_key = KINDS[kind][1]
    if not {'Time', magnitude_key, 'Location', 'State', 'Lat', 'Lon'}.issubset(reader.fieldnames or []):
        raise RuntimeError('NOAA returned an unexpected report format')
    reports = []
    for row in reader:
        try:
            lat, lon = float(row.get('Lat') or ''), float(row.get('Lon') or '')
        except (ValueError, TypeError):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        raw_time = (row.get('Time') or '').strip()
        occurred = None
        if re.fullmatch(r'\d{4}', raw_time):
            hour, minute = int(raw_time[:2]), int(raw_time[2:])
            if hour < 24 and minute < 60:
                event_day = day + timedelta(days=hour < 12)
                occurred = datetime.combine(event_day, time(hour, minute), timezone.utc).isoformat()
        magnitude = (row.get(magnitude_key) or '').strip()
        value = None
        try:
            value = float(magnitude)
            if not math.isfinite(value) or value < 0:
                value = None
        except ValueError:
            pass
        if kind == 'hail':
            value = value / 100 if value is not None else None
            label = f'{value:g} in' if value is not None else 'Unknown'
        elif kind == 'wind':
            label = f'{value:g} kt' if value is not None else 'Unknown / damage report'
        else:
            label = 'Unrated' if magnitude in ('', 'UNK', '-9') else f'Reported scale: {magnitude}'
        reports.append({
            'time': raw_time, 'occurred_at': occurred, 'magnitude': magnitude,
            'magnitude_label': label, 'hail_inches': value if kind == 'hail' else None,
            'wind_knots': value if kind == 'wind' else None,
            'location': row.get('Location') or '', 'county': row.get('County') or '',
            'state': row.get('State') or '', 'latitude': lat, 'longitude': lon,
            'comments': row.get('Comments') or '', 'kind': kind, 'ground_verified': False,
            'source': 'NOAA/NWS SPC preliminary report',
        })
    return reports


def fetch_spc_reports(day: date, kind: str = 'hail'):
    url = _url_for(day, kind)
    key = (day, kind)
    with _lock:
        cached = _cache.get(key)
        if cached and monotonic() - cached[0] < TTL_SECONDS:
            return deepcopy(cached[1])
    response = httpx.get(url, timeout=20, follow_redirects=True,
                         headers={'User-Agent': 'RoofBrokersCRM/3.7'})
    response.raise_for_status()
    reports = parse_spc_csv(response.text, day, kind)
    result = {
        'date': day.isoformat(), 'kind': kind, 'source_url': url,
        'count': len(reports), 'reports': reports,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'period_start': datetime.combine(day, time(12), timezone.utc).isoformat(),
        'period_end': datetime.combine(day + timedelta(days=1), time(12), timezone.utc).isoformat(),
        'note': 'Preliminary reports; not a damage footprint or property-level verification.',
    }
    with _lock:
        if len(_cache) >= 128:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (monotonic(), deepcopy(result))
    return result
