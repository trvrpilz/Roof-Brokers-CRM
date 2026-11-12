from pathlib import Path

index = Path('/runtime/web/index.html')
html = index.read_text()
if html.count('</body>') != 1 or 'id="leadStatus"' not in html:
    raise SystemExit('owner-assignment UI patch: expected CRM markup missing')

script = r"""
<style>
.rb-assignment{margin:12px 0;padding:12px;border:1px solid #cbd5e1;border-radius:10px;background:#f8fafc}
.rb-assignment label{display:block;font-size:13px;font-weight:700;margin-bottom:7px}
.rb-assignment-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.rb-assignment-row select{min-width:170px;max-width:100%;flex:1;padding:9px}
.rb-assignment-row button{padding:9px 13px}
.rb-assignment-note{font-size:12px;margin-top:7px;color:#475569}
</style>
<script>
(() => {
  // Purely an owner convenience UI. /api/users and the assignment endpoint
  // independently require OWNER authorization on the server.
  let users = [];
  let activeLead = null;
  let busy = false;
  let initialized = false;
  const assignmentId = 'rb-assignment';
  function owner() {
    return typeof currentUser !== 'undefined' &&
      currentUser && String(currentUser.role || '').toUpperCase() === 'OWNER';
  }
  function getSelected() {
    return typeof selectedLead !== 'undefined' ? selectedLead : null;
  }
  function note(value, error = false) {
    const el = document.getElementById('rb-assignment-note');
    if (el) {
      el.textContent = value;
      el.style.color = error ? '#b91c1c' : '#475569';
    }
  }
  async function refreshUsers() {
    if (!owner()) return;
    try {
      const result = await api('/api/users');
      users = Array.isArray(result) ? result.filter(u => u.active) : [];
      render();
    } catch (err) {
      note('Unable to load team members: ' + (err.message || err), true);
    }
  }
  function render() {
    const host = document.getElementById(assignmentId);
    if (!host || !owner()) return;
    const lead = getSelected();
    const leadId = lead && lead.id;
    const select = host.querySelector('select');
    const save = host.querySelector('button');
    host.hidden = !leadId;
    if (!leadId) return;
    if (!busy || activeLead !== leadId) {
      select.replaceChildren();
      for (const user of users) {
        const opt = new Option(user.name + ' (' + user.role + ')', user.id);
        select.add(opt);
      }
      const current = lead.assigned_user_id;
      if (current && !users.some(u => u.id === current)) {
        select.add(new Option('Previous/inactive assignee', current));
      }
      if (current) select.value = current;
      activeLead = leadId;
    }
    select.disabled = busy || !users.length;
    save.disabled = busy || !users.length;
    if (!users.length) note('No active team members available.');
    else if (!busy) note('Only the owner can change lead assignments.');
  }
  async function saveAssignment() {
    if (busy || !owner()) return;
    const lead = getSelected();
    const select = document.querySelector('#' + assignmentId + ' select');
    const target = select?.value;
    if (!lead?.id || !target) return;
    busy = true;
    render();
    note('Saving assignment…');
    try {
      const result = await api('/api/leads/' + encodeURIComponent(lead.id) + '/assignment', {
        method: 'PATCH',
        body: {assigned_user_id: target}
      });
      if (typeof selectedLead !== 'undefined' && selectedLead?.id === lead.id) {
        selectedLead.assigned_user_id = result.assigned_user_id;
      }
      activeLead = null;
      busy = false;
      render();
      note('Assignment saved. The representative can now access this lead.');
    } catch (err) {
      busy = false;
      render();
      note('Unable to save assignment: ' + (err.message || err), true);
    }
  }
  function initialize() {
    if (initialized || !owner()) return;
    const status = document.getElementById('leadStatus');
    if (!status) return;
    const host = document.createElement('section');
    host.id = assignmentId;
    host.className = 'rb-assignment';
    host.hidden = true;
    const heading = document.createElement('label');
    heading.textContent = 'Assigned team member';
    heading.htmlFor = 'rb-assigned-user';
    const row = document.createElement('div');
    row.className = 'rb-assignment-row';
    const select = document.createElement('select');
    select.id = 'rb-assigned-user';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'secondary';
    button.textContent = 'Assign lead';
    button.addEventListener('click', saveAssignment);
    row.append(select, button);
    const message = document.createElement('div');
    message.id = 'rb-assignment-note';
    message.className = 'rb-assignment-note';
    host.append(heading, row, message);
    status.parentElement.insertAdjacentElement('afterend', host);
    initialized = true;
    const detailName = document.getElementById('leadName');
    if (detailName) new MutationObserver(() => queueMicrotask(render))
      .observe(detailName, {childList: true, characterData: true, subtree: true});
    // Lead status options refresh whenever another lead is selected.
    new MutationObserver(() => queueMicrotask(render))
      .observe(status, {childList: true});
    refreshUsers();
    render();
  }
  // Existing app sets currentUser after authentication; do not ask rep accounts
  // for the owner-only /api/users endpoint.
  const check = setInterval(() => {
    if (initialized || (typeof currentUser !== 'undefined' && currentUser && !owner())) {
      clearInterval(check);
      return;
    }
    initialize();
  }, 500);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && initialized && owner()) refreshUsers();
  });
})();
</script>
"""
html = html.replace('</body>', script + '\n</body>')
index.write_text(html)
print('owner_assignment36: owner-only lead reassignment selector installed')
