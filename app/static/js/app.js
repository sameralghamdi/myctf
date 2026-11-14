// MyCTF front-end helpers. Auth is cookie-based (HttpOnly), so fetch() just needs
// credentials:'same-origin'. These power the challenge play screen.

async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || 'GET',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    credentials: 'same-origin',
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (e) { /* non-json */ }
  return { ok: res.ok, status: res.status, data };
}

function toast(msg, kind = 'info') {
  const t = document.createElement('div');
  t.className = 'alert ' + (kind === 'ok' ? 'ok' : kind === 'err' ? 'err' : 'info');
  t.style.cssText = 'position:fixed;right:20px;bottom:20px;z-index:9999;max-width:360px;box-shadow:0 8px 30px rgba(0,0,0,.4)';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 4200);
}

// ---- challenge play screen ----
const Challenge = {
  slug: null,
  async startLab() {
    const { ok, data } = await api(`/api/challenges/${this.slug}/lab/start`, { method: 'POST' });
    if (!ok) return toast(data?.error || 'Could not start lab', 'err');
    this._mountLab(data.url, data.instance_id, data.expires_at);
    toast('Lab started — happy hacking.', 'ok');
  },
  async stopLab(instanceId) {
    const { ok, data } = await api(`/api/labs/${instanceId}/stop`, { method: 'POST' });
    if (!ok) return toast(data?.error || 'Could not stop lab', 'err');
    location.reload();
  },
  async resetLab(instanceId) {
    const { ok, data } = await api(`/api/labs/${instanceId}/reset`, { method: 'POST' });
    if (!ok) return toast(data?.error || 'Could not reset lab', 'err');
    this._mountLab(data.url, data.instance_id, data.expires_at);
    toast('Lab reset with a fresh flag.', 'ok');
    document.getElementById('lab-controls')?.setAttribute('data-instance', data.instance_id);
  },
  _mountLab(url, instanceId, expiresAt) {
    const right = document.getElementById('lab-pane');
    right.innerHTML = `
      <div class="lab-toolbar">
        <span class="dot run"></span> <span>running</span>
        <span class="mono">${instanceId.slice(0,8)}</span>
        <span class="muted">· expires ${expiresAt || ''}</span>
        <span style="margin-left:auto" class="row">
          <a class="btn ghost sm" href="${url}" target="_blank" rel="noopener">Open in tab ↗</a>
          <button class="btn ghost sm" onclick="Challenge.resetLab('${instanceId}')">Restart</button>
          <button class="btn danger sm" onclick="Challenge.stopLab('${instanceId}')">Stop</button>
        </span>
      </div>
      <iframe src="${url}" title="lab"></iframe>`;
  },
  async submitFlag(ev) {
    ev.preventDefault();
    const input = document.getElementById('flag-input');
    const flag = input.value.trim();
    if (!flag) return;
    const { ok, status, data } = await api(`/api/challenges/${this.slug}/submit`, {
      method: 'POST', body: { flag },
    });
    const box = document.getElementById('submit-result');
    if (data?.correct) {
      box.className = 'alert ok';
      box.textContent = data.message;
      if (!data.already_solved) setTimeout(() => location.reload(), 900);
    } else if (status === 429) {
      box.className = 'alert warn';
      box.textContent = data?.error || 'Rate limited — slow down and try again.';
    } else {
      box.className = 'alert err';
      box.textContent = data?.message || data?.error || 'Incorrect.';
    }
    box.style.display = 'block';
  },
  async unlockHint(level, btn) {
    const { ok, data } = await api(`/api/challenges/${this.slug}/hints/${level}`, { method: 'POST' });
    if (!ok) return toast(data?.error || 'Error', 'err');
    const target = document.getElementById(`hint-body-${level}`);
    target.textContent = data.body;
    target.style.display = 'block';
    btn?.remove();
  },
};
