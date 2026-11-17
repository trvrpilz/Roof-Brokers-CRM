/* NOAA reports stay separate from MRMS radar estimates and contractor evidence. */
(() => {
  const button = document.getElementById('noaa');
  const layer = L.layerGroup().addTo(map);
  const colors = {hail: '#b45309', wind: '#2563eb', tornado: '#dc2626'};
  let requestId = 0;
  let loaded = null;
  let reports = [];
  const panel = document.createElement('section');
  panel.id = 'noaaPanel';
  panel.className = 'intel';
  panel.setAttribute('aria-label', 'NOAA storm mapping');
  panel.innerHTML = `
    <button id="noaaClose" class="secondary" style="float:right">Close</button>
    <h3>NOAA Storm Mapping</h3>
    <label for="noaaDay">Storm day</label>
    <input id="noaaDay" type="date" min="1999-06-01" style="display:block;padding:10px;margin:6px 0 12px;max-width:100%;box-sizing:border-box">
    <label for="noaaKind">Report type</label>
    <select id="noaaKind" style="display:block;margin:6px 0 12px"><option value="hail">Hail</option><option value="wind">Wind</option><option value="tornado">Tornado</option></select>
    <p class="muted">A storm day runs from 12:00 UTC to 12:00 UTC the next day. Hail sizes are inches; wind speeds are knots.</p>
    <button id="noaaLoad">Load reports</button> <button id="noaaClear" class="secondary">Clear layer</button>
    <p id="noaaStatus" role="status" aria-live="polite">Choose a storm day and load NOAA reports.</p>
    <p id="noaaViewport" class="muted"></p>
    <button id="noaaFit" class="secondary" disabled>Show all loaded reports</button>
    <p><a id="noaaSource" target="_blank" rel="noopener noreferrer" hidden>Open NOAA source CSV</a></p>
    <p class="muted">Orange: hail • Blue: wind • Red: tornado.<br>Preliminary NOAA/NWS reports are points, not damage footprints. Radar estimates and contractor ground evidence remain separate. Loading reports does not create CRM leads.</p>`;
  document.body.append(panel);
  L.DomEvent.disableClickPropagation(panel);
  L.DomEvent.disableScrollPropagation(panel);
  const el = id => document.getElementById(id);
  const currentDay = () => new Date(Date.now() - 12 * 3600000).toISOString().slice(0, 10);
  el('noaaDay').value = el('noaaDay').max = currentDay();
  const status = text => { el('noaaStatus').textContent = text; };
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function countVisible() {
    if (!loaded) { el('noaaViewport').textContent = ''; return; }
    const bounds = map.getBounds();
    const count = reports.filter(r => bounds.contains([r.latitude, r.longitude])).length;
    el('noaaViewport').textContent = `${count} of ${reports.length} loaded ${loaded.kind} reports in this map view • storm day ${loaded.date}`;
  }
  button.onclick = () => {
    const open = panel.style.display !== 'block';
    panel.style.display = open ? 'block' : 'none';
    button.setAttribute('aria-expanded', String(open));
    if (open) { el('noaaDay').max = currentDay(); el('noaaDay').focus(); countVisible(); }
  };
  button.setAttribute('aria-controls', panel.id);
  button.setAttribute('aria-expanded', 'false');
  el('noaaClose').onclick = () => { panel.style.display = 'none'; button.setAttribute('aria-expanded', 'false'); button.focus(); };
  panel.addEventListener('keydown', event => { if (event.key === 'Escape') el('noaaClose').click(); });
  el('noaaClear').onclick = () => {
    requestId++;
    layer.clearLayers(); reports = []; loaded = null;
    el('noaaSource').hidden = true; el('noaaFit').disabled = true;
    el('noaaLoad').disabled = false;
    status('NOAA report layer cleared.'); countVisible();
  };
  el('noaaFit').onclick = () => {
    if (reports.length) map.fitBounds(L.latLngBounds(reports.map(r => [r.latitude, r.longitude])), {padding: [40, 40], maxZoom: 12});
  };
  map.on('moveend', countVisible);
  el('noaaLoad').onclick = async () => {
    const day = el('noaaDay').value, kind = el('noaaKind').value;
    if (!el('noaaDay').checkValidity() || !day || day > currentDay()) {
      status('Choose a valid storm day through the current NOAA storm day.'); return;
    }
    const id = ++requestId;
    el('noaaLoad').disabled = true;
    status(`Loading NOAA ${kind} reports for ${day}…`);
    try {
      const data = await api(`/api/noaa/spc-reports?day=${encodeURIComponent(day)}&kind=${encodeURIComponent(kind)}`);
      if (id !== requestId) return;
      if (!Array.isArray(data.reports)) throw new Error('Unexpected NOAA response');
      const next = data.reports.filter(r => Number.isFinite(r.latitude) && Number.isFinite(r.longitude) && Math.abs(r.latitude) <= 90 && Math.abs(r.longitude) <= 180);
      layer.clearLayers(); reports = next; loaded = {date: data.date, kind: data.kind};
      for (const r of reports) {
        const eventTime = r.occurred_at ? new Date(r.occurred_at).toLocaleString() : `${r.time || 'Unknown'} UTC`;
        L.circleMarker([r.latitude, r.longitude], {radius: 7, color: colors[kind], fillOpacity: .55})
          .addTo(layer).bindPopup(`<b>NOAA/NWS preliminary ${escape(kind)} report</b><br>${escape(r.location)} ${escape(r.state)}<br>${escape(eventTime)}<br>${escape(r.magnitude_label)}<br>${escape(r.comments)}<br><small>Reported location; property damage is unverified.</small>`);
      }
      const source = el('noaaSource');
      source.href = `https://www.spc.noaa.gov/climo/reports/${day.slice(2).replaceAll('-', '')}_rpts_${({hail:'hail',wind:'wind',tornado:'torn'})[kind]}.csv`;
      source.hidden = false;
      el('noaaFit').disabled = !reports.length;
      const fetched = data.fetched_at ? ` Retrieved ${new Date(data.fetched_at).toLocaleString()}.` : '';
      status(reports.length ? `Loaded ${reports.length} ${kind} reports for ${day}.${fetched}` : `NOAA returned no ${kind} reports for storm day ${day}.${fetched}`);
      countVisible();
    } catch (error) {
      if (id !== requestId) return;
      status(`Could not load NOAA ${kind} reports for ${day}. ${loaded ? `Still showing ${loaded.kind} reports for ${loaded.date}.` : 'No NOAA reports are displayed.'} Try again when online.`);
    } finally {
      if (id === requestId) el('noaaLoad').disabled = false;
    }
  };
})();
