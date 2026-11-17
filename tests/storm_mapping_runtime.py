"""SPC parsing and fetch tests: no network, credentials, or production writes."""
import importlib.util
import os
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch, Mock

path = Path(os.getenv('RB_SPC_MODULE', '/srv/backend/app/spc_reports.py'))
spec = importlib.util.spec_from_file_location('spc_reports', path)
spc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spc)

hail = 'Time,Size,Location,County,State,Lat,Lon,Comments\n2359,175,Sample,County,IL,42,-88,"Hail, measured"\n0015,100,Next day,County,WI,43,-89,Reported\n1200,UNK,Unknown,County,WI,43,-89,Unknown size\n1300,200,Bad,County,WI,nan,-89,Invalid\n1300,200,Bad,County,WI,91,-89,Invalid\n'
day = date(2025, 5, 15)
rows = spc.parse_spc_csv(hail, day, 'hail')
assert len(rows) == 3
assert rows[0]['hail_inches'] == 1.75
assert rows[0]['magnitude_label'] == '1.75 in'
assert rows[0]['comments'] == 'Hail, measured'
assert rows[0]['occurred_at'] == '2025-05-15T23:59:00+00:00'
assert rows[1]['occurred_at'] == '2025-05-16T00:15:00+00:00'
assert rows[2]['hail_inches'] is None
assert rows[2]['ground_verified'] is False
assert spc.current_report_day(datetime(2026, 11, 17, 11, 59, tzinfo=timezone.utc)) == date(2026, 11, 16)
assert spc.current_report_day(datetime(2026, 11, 17, 12, tzinfo=timezone.utc)) == date(2026, 11, 17)
wind = spc.parse_spc_csv('Time,Speed,Location,State,Lat,Lon\n1300,60,Here,IL,42,-88\n1400,UNK,There,IL,42,-88\n', day, 'wind')
assert wind[0]['wind_knots'] == 60 and wind[0]['magnitude_label'] == '60 kt'
assert wind[1]['wind_knots'] is None
tornado = spc.parse_spc_csv('Time,F_Scale,Location,State,Lat,Lon\n1300,UNK,Here,IL,42,-88\n', day, 'tornado')
assert tornado[0]['magnitude_label'] == 'Unrated'
assert spc.parse_spc_csv('Time,Size,Location,State,Lat,Lon\n', day, 'hail') == []
for invalid in ['<html>unavailable</html>', 'Time,Size\n1300,100\n']:
    try:
        spc.parse_spc_csv(invalid, day, 'hail')
        raise AssertionError('Unexpected NOAA format accepted')
    except RuntimeError:
        pass
for bad_day, bad_kind in [(date(2099, 1, 1), 'hail'), (date(1999, 5, 31), 'hail'), (day, 'other')]:
    try:
        spc._url_for(bad_day, bad_kind)
        raise AssertionError('Invalid request accepted')
    except ValueError:
        pass
response = Mock(text=hail)
with patch.object(spc.httpx, 'get', return_value=response) as get:
    result = spc.fetch_spc_reports(day)
    assert get.call_args.args[0] == 'https://www.spc.noaa.gov/climo/reports/250515_rpts_hail.csv'
    assert result['count'] == 3 and result['period_end'] == '2025-05-16T12:00:00+00:00'
    result['reports'].clear()
    assert len(spc.fetch_spc_reports(day)['reports']) == 3
    assert get.call_count == 1
print('NOAA storm mapping: parsing, units, storm-day rollover, validation, empty responses and cache passed')
