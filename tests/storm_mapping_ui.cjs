// Exercise real UI event handlers without a browser, NOAA calls, or CRM writes.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {style: {}, value: '', disabled: false, hidden: false,
    setAttribute() {}, addEventListener() {}, focus() {}, checkValidity: () => true});
  return elements.get(id);
}
const markers = [];
let clearCount = 0, fetchCount = 0, reply;
const layer = {addTo() {return this;}, clearLayers() {markers.length = 0; clearCount++;}};
const context = {
  document: {getElementById: element, createElement: () => element('panel'), body: {append() {}}},
  L: {layerGroup: () => layer, DomEvent: {disableClickPropagation() {}, disableScrollPropagation() {}},
    circleMarker: (coords, options) => ({addTo() {return this;}, bindPopup(html) {markers.push({coords, options, html});}}),
    latLngBounds: points => points},
  map: {on() {}, getBounds: () => ({contains: () => true}), fitBounds() {}},
  api: async () => {fetchCount++; if (reply instanceof Error) throw reply; return await reply;},
  Date, Number, String,
};
vm.runInNewContext(fs.readFileSync(process.env.RB_STORM_JS || '.staging/storm_mapping37/storm-mapping.js', 'utf8'), context);
const get = element;
const response = {date: '2025-05-15', kind: 'hail', reports: [{latitude:42, longitude:-88,
  location:'<img src=x onerror=alert(1)>', state:'IL', comments:'<script>bad</script>', magnitude_label:'1.75 in'}]};
(async () => {
  get('noaaDay').value = response.date; get('noaaKind').value = 'hail'; reply = response;
  await get('noaaLoad').onclick();
  assert.equal(markers.length, 1);
  assert(markers[0].html.includes('1.75 in'));
  assert(!markers[0].html.includes('<script>'));
  assert(markers[0].html.includes('&lt;img'));
  await get('noaaLoad').onclick();
  assert.equal(markers.length, 1, 'Reload must replace rather than duplicate markers');
  reply = new Error('offline'); get('noaaDay').value = '2025-05-16';
  await get('noaaLoad').onclick();
  assert(get('noaaStatus').textContent.includes('Still showing hail reports for 2025-05-15'));
  assert.equal(markers.length, 1);
  let resolve;
  reply = new Promise(r => {resolve = r;});
  const pending = get('noaaLoad').onclick();
  get('noaaClear').onclick(); resolve(response); await pending;
  assert.equal(markers.length, 0, 'Clear must invalidate in-flight request');
  assert(get('noaaSource').hidden);
  assert(!get('noaaLoad').disabled);
  reply = {...response, reports: []}; await get('noaaLoad').onclick();
  assert(get('noaaStatus').textContent.includes('no hail reports'));
  assert(get('noaaFit').disabled);
  get('noaaDay').value = '2099-01-01'; const before = fetchCount;
  await get('noaaLoad').onclick(); assert.equal(fetchCount, before);
  assert(clearCount >= 3);
  console.log('NOAA UI: marker replacement, escaped popups, failed reload, clear while loading, empty results and future dates passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
