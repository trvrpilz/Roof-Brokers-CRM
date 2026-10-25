from pathlib import Path

ROOT = Path('/runtime')
INDEX = ROOT / 'web/index.html'
MAP = ROOT / 'web/map.html'
MAIN = ROOT / 'backend/app/main.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Build 3.3 patch mismatch for {label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


idx = INDEX.read_text()
idx = replace_once(
    idx,
    'Staging Build 3.1 • CRM + Field + Storm Intelligence + AccuLynx safety gates',
    'Staging Build 3.3 • Field UX + CRM + Storm Intelligence + AccuLynx safety gates',
    'build label',
)

css = r'''
.search{min-width:220px;flex:1;max-width:380px}
.section-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
.quickbar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.quickbar a,.quickbar button{display:inline-flex;align-items:center;justify-content:center;text-decoration:none}
.quickbar a[aria-disabled="true"]{opacity:.45;pointer-events:none}
.lead.active{background:#f1f7f4;margin:0 -10px;padding:12px 10px;border-radius:10px}
.lead button{max-width:150px}
.empty-state{padding:18px 0;text-align:center}
.activity{display:grid;gap:8px;margin-top:10px}
.activity-item{border:1px solid var(--line);border-radius:10px;padding:10px;background:#fafbfc}
.activity-item b{display:block;font-size:13px}.activity-item span{font-size:12px;color:var(--muted)}
.mobile-nav{display:none}
@media(max-width:760px){
 header{padding:10px 12px}.brand-logo{height:42px}.sub{font-size:11px}
 .toolbar{position:sticky;top:65px;z-index:2;background:var(--bg);padding:8px 0;margin-bottom:8px}
 .toolbar .muted{display:none}.search{order:5;flex-basis:100%;max-width:none}
 .user-tools{margin-left:0;width:100%}.user-pill{flex:1}
 .quickbar{display:grid;grid-template-columns:1fr 1fr}.quickbar>*{width:100%}
 .tabs{position:sticky;top:126px;z-index:1;background:var(--card);padding:6px 0}
 .lead{align-items:center}.lead button{font-size:12px;padding:8px}
 .mobile-nav{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;position:sticky;bottom:8px;z-index:4;margin-top:12px}
 .mobile-nav button{box-shadow:0 4px 18px #0002}
}
'''
idx = replace_once(idx, '</style>', css + '\n</style>', 'field UX CSS')

idx = replace_once(
    idx,
    '<button class="primary" id="newLead">+ New Lead</button>\n<button class="secondary" id="stormBtn">Storm Map</button>\n<span class="muted">Company data is isolated by tenant.</span>',
    '<button class="primary" id="newLead">+ New Lead</button>\n<button class="secondary" id="stormBtn">Field Map</button>\n<input class="search" id="leadSearch" type="search" placeholder="Search leads, address, phone…" aria-label="Search leads">\n<span class="muted">Company data is isolated by tenant.</span>',
    'toolbar search',
)
idx = replace_once(
    idx,
    '<h3>Leads & Properties</h3>\n<div id="leadList"></div>',
    '<div class="section-head"><h3>Leads & Properties</h3><span class="muted" id="leadCount"></span></div>\n<div id="leadList"></div>',
    'lead count',
)
status_line = '<div style="margin-top:10px"><select id="leadStatus" aria-label="Pipeline status"></select> <span class="muted" id="saveState"></span></div>'
idx = replace_once(
    idx,
    status_line,
    status_line + '''\n<div class="quickbar" id="quickbar">\n<a class="secondary" id="quickCall" href="#" aria-disabled="true">Call</a>\n<a class="secondary" id="quickText" href="#" aria-disabled="true">Text</a>\n<button class="secondary" id="quickInspect" type="button">Start / Open Inspection</button>\n<button class="secondary" id="quickMap" type="button">Open Field Map</button>\n</div>''',
    'quick actions',
)
idx = replace_once(
    idx,
    '<button class="tab" data-tab="acculynx">AccuLynx</button>',
    '<button class="tab" data-tab="activity">Activity</button>\n<button class="tab" data-tab="acculynx">AccuLynx</button>',
    'activity tab',
)
idx = replace_once(
    idx,
    '<div class="panel" id="acculynx">',
    '''<div class="panel" id="activity">\n<div class="section-head"><h3>Lead Activity</h3><button class="secondary" id="refreshActivity" type="button">Refresh</button></div>\n<div class="activity" id="activityList"><div class="muted">Select a lead to view activity.</div></div>\n</div>\n\n<div class="panel" id="acculynx">''',
    'activity panel',
)
idx = replace_once(
    idx,
    '</main>',
    '''<div class="mobile-nav">\n<button class="primary" id="mobileNewLead" type="button">New Lead</button>\n<button class="secondary" id="mobileMap" type="button">Field Map</button>\n<button class="secondary" id="mobileInspect" type="button">Inspection</button>\n</div>\n</main>''',
    'mobile nav',
)
idx = replace_once(
    idx,
    'let companyId=null, leads=[], selectedLeadId=null, selectedLead=null, activeInspectionId=null, currentUser=null;',
    "let companyId=null, leads=[], selectedLeadId=null, selectedLead=null, activeInspectionId=null, currentUser=null;\nconst requestedLeadId=new URLSearchParams(location.search).get('lead');",
    'deep link state',
)
idx = replace_once(
    idx,
    "async function loadCompany(){companyId=$('company').value;const [ls,dash,conns]=await Promise.all([api('/api/leads'),api('/api/dashboard'),api('/api/acculynx-connections')]);leads=ls;renderLeads();renderPipeline(dash.pipeline);$('axDest').innerHTML=conns.length?conns.map(c=>`<option value=\"${c.id}\">${c.label}</option>`).join(''):'<option value=\"\">No AccuLynx destinations configured</option>';if(leads.length)await selectLead(leads[0].id);else clearDetail();}",
    "async function loadCompany(){companyId=$('company').value;const [ls,dash,conns]=await Promise.all([api('/api/leads'),api('/api/dashboard'),api('/api/acculynx-connections')]);leads=ls;renderLeads();renderPipeline(dash.pipeline);$('axDest').innerHTML=conns.length?conns.map(c=>`<option value=\"${c.id}\">${c.label}</option>`).join(''):'<option value=\"\">No AccuLynx destinations configured</option>';if(leads.length){const target=leads.some(x=>x.id===requestedLeadId)?requestedLeadId:(selectedLeadId&&leads.some(x=>x.id===selectedLeadId)?selectedLeadId:leads[0].id);await selectLead(target);}else clearDetail();}",
    'deep link selection',
)
idx = replace_once(
    idx,
    "function renderLeads(){$('leadList').innerHTML=leads.length?'':'<div class=\"muted\">No leads yet.</div>';leads.forEach(l=>{const row=document.createElement('div');row.className='lead';row.innerHTML=`<div><b>${l.name}</b><div class=\"muted\">${address(l)}</div></div><button class=\"secondary\">${l.status}</button>`;row.querySelector('button').onclick=()=>selectLead(l.id);$('leadList').append(row);});}",
    "function renderLeads(){const q=($('leadSearch')?.value||'').trim().toLowerCase();const rows=leads.filter(l=>!q||[l.name,address(l),l.phone,l.email,l.status].filter(Boolean).join(' ').toLowerCase().includes(q));$('leadCount').textContent=q?`${rows.length} of ${leads.length}`:`${leads.length} total`;$('leadList').innerHTML=rows.length?'':`<div class=\"muted empty-state\">${leads.length?'No matching leads.':'No leads yet. Create your first lead to begin.'}</div>`;rows.forEach(l=>{const row=document.createElement('div');row.className='lead'+(l.id===selectedLeadId?' active':'');row.innerHTML=`<div><b>${l.name}</b><div class=\"muted\">${address(l)}</div><div class=\"muted\">${l.phone||''}</div></div><button class=\"secondary\">${l.status}</button>`;row.onclick=()=>selectLead(l.id);$('leadList').append(row);});}",
    'lead search rendering',
)
idx = replace_once(
    idx,
    "function clearDetail(){$('leadName').textContent='No lead selected';$('leadAddress').textContent='Create a lead to begin.'}",
    "function clearDetail(){selectedLeadId=null;selectedLead=null;$('leadName').textContent='No lead selected';$('leadAddress').textContent='Create a lead to begin.';$('quickCall').setAttribute('aria-disabled','true');$('quickText').setAttribute('aria-disabled','true');$('activityList').innerHTML='<div class=\"muted\">Select a lead to view activity.</div>';renderLeads();}",
    'empty lead state',
)
idx = replace_once(
    idx,
    "async function selectLead(id){selectedLeadId=id;selectedLead=await api(`/api/leads/${id}`);$('leadName').textContent=selectedLead.name;$('leadAddress').textContent=address(selectedLead);$('detailPhone').value=selectedLead.phone||'';$('detailEmail').value=selectedLead.email||'';$('leadStatus').innerHTML=PIPELINE.map(s=>`<option ${s===selectedLead.status?'selected':''}>${s}</option>`).join('');const c=selectedLead.claim||{};$('claimCarrier').value=c.carrier||'';$('claimNumber').value=c.claim_number||'';$('claimDate').value=c.date_of_loss||'';$('claimLoss').value=c.loss_type||'';$('claimAdjuster').value=c.adjuster||'';$('claimDeductible').value=c.deductible||'';const ax=selectedLead.acculynx;$('axStatus').textContent=ax?`${ax.status}${ax.remote_job_id?' — '+ax.remote_job_id:''}`:'NOT LINKED';$('axStatus').className=ax?'ok':'';await Promise.all([loadObservations(),loadMedia(),loadInspections()]);}",
    "async function selectLead(id){selectedLeadId=id;selectedLead=await api(`/api/leads/${id}`);$('leadName').textContent=selectedLead.name;$('leadAddress').textContent=address(selectedLead);$('detailPhone').value=selectedLead.phone||'';$('detailEmail').value=selectedLead.email||'';$('leadStatus').innerHTML=PIPELINE.map(s=>`<option ${s===selectedLead.status?'selected':''}>${s}</option>`).join('');const phone=(selectedLead.phone||'').replace(/[^+\\d]/g,'');$('quickCall').href=phone?`tel:${phone}`:'#';$('quickText').href=phone?`sms:${phone}`:'#';$('quickCall').setAttribute('aria-disabled',phone?'false':'true');$('quickText').setAttribute('aria-disabled',phone?'false':'true');const c=selectedLead.claim||{};$('claimCarrier').value=c.carrier||'';$('claimNumber').value=c.claim_number||'';$('claimDate').value=c.date_of_loss||'';$('claimLoss').value=c.loss_type||'';$('claimAdjuster').value=c.adjuster||'';$('claimDeductible').value=c.deductible||'';const ax=selectedLead.acculynx;$('axStatus').textContent=ax?`${ax.status}${ax.remote_job_id?' — '+ax.remote_job_id:''}`:'NOT LINKED';$('axStatus').className=ax?'ok':'';renderLeads();await Promise.all([loadObservations(),loadMedia(),loadInspections(),loadActivity()]);}",
    'lead quick actions',
)
obs = "async function loadObservations(){if(!selectedLeadId)return;const rows=await api(`/api/leads/${selectedLeadId}/ground-observations`);const verified=rows.filter(x=>x.verified).length;const measured=rows.filter(x=>x.measured_hail_inches!=null);const max=measured.length?Math.max(...measured.map(x=>x.measured_hail_inches)):null;$('groundSummary').textContent=`${rows.length} field report${rows.length===1?'':'s'} • ${verified} verified${max?` • largest measured hail ${max.toFixed(2)} in`:''}`;}"
idx = replace_once(
    idx,
    obs,
    obs + "\nasync function loadActivity(){if(!selectedLeadId)return;const rows=await api(`/api/leads/${selectedLeadId}/activity`);$('activityList').innerHTML=rows.length?'':'<div class=\"muted\">No activity recorded yet.</div>';rows.slice(0,30).forEach(x=>{const d=document.createElement('div');d.className='activity-item';const when=x.created_at?new Date(x.created_at).toLocaleString():'';d.innerHTML=`<b>${String(x.event_type||x.action||'Activity').replaceAll('_',' ')}</b><span>${x.description||x.details||''}${when?` • ${when}`:''}</span>`;$('activityList').append(d);});}",
    'activity loader',
)
idx = replace_once(
    idx,
    "$('company').addEventListener('change',loadCompany);",
    "$('company').addEventListener('change',loadCompany);\n$('leadSearch').addEventListener('input',renderLeads);\n$('refreshActivity').onclick=loadActivity;",
    'lead search events',
)
tabs = "document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));btn.classList.add('active');$(btn.dataset.tab).classList.add('active');}));"
idx = replace_once(
    idx,
    tabs,
    tabs + "\nfunction openTab(name){const btn=document.querySelector(`.tab[data-tab=\"${name}\"]`);if(btn)btn.click();}\n$('quickInspect').onclick=async()=>{if(!selectedLeadId)return;if(!activeInspectionId)await $('startInspection').onclick();openTab('photos');};\n$('quickMap').onclick=()=>window.open('/assets/map.html','_blank');\n$('mobileNewLead').onclick=()=>$('newLead').click();\n$('mobileMap').onclick=()=>$('stormBtn').click();\n$('mobileInspect').onclick=()=>$('quickInspect').click();",
    'quick action events',
)
INDEX.write_text(idx)

mp = MAP.read_text()
mp = replace_once(
    mp,
    '</style></head>',
    '@media(max-width:760px){.bar{left:8px;right:8px;top:8px;display:flex;overflow-x:auto;flex-wrap:nowrap;padding:8px}.bar b{display:none}.bar button,.bar .pill{white-space:nowrap;flex:0 0 auto}.panel,.intel{right:8px;left:8px;width:auto;top:auto;bottom:8px;max-height:55vh}.leaflet-control-zoom{margin-top:72px!important}.legend{max-width:210px}.panel .row{position:sticky;bottom:0;background:#fff;padding-top:6px}} </style></head>',
    'map mobile CSS',
)
legacy = "const token=localStorage.getItem('rb_token'); if(!token) location.href='/';\nconst H={'Authorization':'Bearer '+token};\nasync function api(path,opts={}){opts.headers={...H,...(opts.headers||{})};if(opts.body&&typeof opts.body!=='string'){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(opts.body)}const r=await fetch(path,opts);if(!r.ok)throw new Error(await r.text());return r.json()}"
secure = "async function api(path,opts={}){opts.headers={...(opts.headers||{})};if(opts.body&&typeof opts.body!=='string'){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(opts.body)}const r=await fetch(path,{...opts,credentials:'same-origin'});if(r.status===401){location.href='/?returnTo='+encodeURIComponent(location.pathname+location.search);throw new Error('Authentication required')}if(!r.ok){let msg=r.statusText;try{const x=await r.json();msg=x.detail||JSON.stringify(x)}catch{try{msg=await r.text()}catch{}}throw new Error(msg)}return r.status===204?null:r.json()}"
mp = replace_once(mp, legacy, secure, 'secure map auth')
mp = replace_once(
    mp,
    "function updateNet(){const n=document.getElementById('net');n.textContent=navigator.onLine?'Online':'Offline • queued';n.className='pill'+(navigator.onLine?'':' offline')}",
    "function updateNet(){const n=document.getElementById('net'),q=JSON.parse(localStorage.getItem('rb_offline_queue')||'[]').length;n.textContent=navigator.onLine?(q?`Online • ${q} queued`:'Online'):`Offline • ${q} queued`;n.className='pill'+(navigator.onLine?'':' offline')}",
    'map queue status',
)
mp = replace_once(
    mp,
    "function queue(item){const q=JSON.parse(localStorage.getItem('rb_offline_queue')||'[]');q.push(item);localStorage.setItem('rb_offline_queue',JSON.stringify(q));}",
    "function queue(item){const q=JSON.parse(localStorage.getItem('rb_offline_queue')||'[]');q.push(item);localStorage.setItem('rb_offline_queue',JSON.stringify(q));updateNet()}",
    'map queue counter',
)
mp = replace_once(
    mp,
    "localStorage.setItem('rb_offline_queue',JSON.stringify(left));if(q.length!==left.length)loadAll()",
    "localStorage.setItem('rb_offline_queue',JSON.stringify(left));updateNet();if(q.length!==left.length)loadAll()",
    'map queue flush status',
)
MAP.write_text(mp)

main = MAIN.read_text()
main = main.replace("version='3.2.0'", "version='3.3.0'")
main = main.replace("'version':'3.2.0'", "'version':'3.3.0'")
if "3.3.0" not in main:
    raise SystemExit('Build 3.3 version patch failed')
MAIN.write_text(main)

print('Build 3.3 field UX patch applied')
