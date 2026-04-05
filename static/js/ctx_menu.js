/* ─── Shared context menu + Quick Facturas modal ───────────────────────────── */

// ── State ──────────────────────────────────────────────────────────────────────
window._ctx = {
  txId:      null,
  tx:        null,
  accountId: null,
  tags:      [],      // all available tags for this account
  reload:    null,    // function to call after a change (set by each page)
};

// ── Open context menu ──────────────────────────────────────────────────────────
function openCtxMenu(tx, accountId, allTags, clientX, clientY) {
  window._ctx.txId      = tx.id;
  window._ctx.tx        = tx;
  window._ctx.accountId = accountId;
  window._ctx.tags      = allTags || [];

  // Header
  const sign     = tx.is_income ? '+' : '−';
  const amtCls   = tx.is_income ? 'color:var(--green)' : 'color:var(--red)';
  document.getElementById('ctxTxConcepto').textContent = tx.concepto || '—';
  document.getElementById('ctxTxMeta').innerHTML =
    `${tx.fecha} · <span style="${amtCls};font-weight:600">${sign}${_ctxFmt(Math.abs(tx.importe))}</span>`;

  _ctxRenderTags();
  const inp = document.getElementById('ctxTagInput');
  inp.value = '';
  document.getElementById('ctxTagDropdown').style.display = 'none';

  // Button callbacks
  document.getElementById('ctxBtnFacturas').onclick = () => { _ctxClose(); openQfModal(tx.id, tx, accountId); };
  document.getElementById('ctxBtnDetail').onclick   = () => { _ctxClose(); if (typeof openTxDetail === 'function') openTxDetail(tx.id); };
  document.getElementById('ctxBtnDelete').onclick   = () => { _ctxClose(); if (typeof deleteTx === 'function') deleteTx(tx.id); };

  // Position
  const menu = document.getElementById('txCtxMenu');
  menu.style.display = 'block';
  requestAnimationFrame(() => {
    const x = Math.min(clientX, window.innerWidth  - menu.offsetWidth  - 8);
    const y = Math.min(clientY, window.innerHeight - menu.offsetHeight - 8);
    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';
  });
}

function _ctxClose() {
  const m = document.getElementById('txCtxMenu');
  if (m) m.style.display = 'none';
}

// ── Tag rendering ──────────────────────────────────────────────────────────────
function _ctxRenderTags() {
  const tags = window._ctx.tx?.tags || [];
  const c    = document.getElementById('ctxCurrentTags');
  if (!c) return;
  if (!tags.length) {
    c.innerHTML = '<span style="font-size:11px;color:var(--text-muted)">Sin etiquetas</span>';
    return;
  }
  c.innerHTML = tags.map(t => `
    <span style="display:inline-flex;align-items:center;gap:3px;background:${t.color}22;color:${t.color};
                 border:1px solid ${t.color}44;border-radius:4px;padding:2px 6px;font-size:11.5px">
      ${_ctxEsc(t.name)}
      <button onclick="_ctxRemoveTag(${t.id})"
              style="background:none;border:none;cursor:pointer;color:${t.color};padding:0;line-height:1;font-size:12px;margin-left:2px"
              title="Quitar etiqueta">✕</button>
    </span>`).join('');
}

async function _ctxRemoveTag(tagId) {
  const {txId, tx} = window._ctx;
  await fetch(`/api/transactions/${txId}/tags/${tagId}`, { method: 'DELETE' });
  tx.tags = (tx.tags || []).filter(t => t.id !== tagId);
  _ctxRenderTags();
  if (window._ctx.reload) window._ctx.reload();
}

// ── Tag search/create input ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const inp = document.getElementById('ctxTagInput');
  const dd  = document.getElementById('ctxTagDropdown');
  if (!inp) return;

  inp.addEventListener('input', () => {
    const q   = inp.value.trim().toLowerCase();
    const {tags, tx} = window._ctx;
    if (!q) { dd.style.display = 'none'; return; }

    const usedIds  = (tx?.tags || []).map(t => t.id);
    const filtered = tags.filter(t => t.name.toLowerCase().includes(q) && !usedIds.includes(t.id));
    const exact    = tags.some(t => t.name.toLowerCase() === q);

    let html = filtered.map(t => `
      <div style="display:flex;align-items:center;gap:6px;padding:7px 10px;cursor:pointer;transition:background .1s"
           onmouseover="this.style.background='rgba(255,255,255,.06)'" onmouseout="this.style.background=''"
           onclick="_ctxAddTag(${t.id},'${_ctxEsc(t.name)}','${t.color}')">
        <span style="width:8px;height:8px;border-radius:50%;background:${t.color};flex-shrink:0"></span>
        <span style="flex:1;font-size:12.5px">${_ctxEsc(t.name)}</span>
        <button onclick="event.stopPropagation();_ctxDeleteTag(${t.id},'${_ctxEsc(t.name)}')"
                style="background:none;border:none;cursor:pointer;color:var(--text-muted);padding:2px 4px;border-radius:4px;font-size:11px"
                title="Borrar etiqueta del sistema" onmouseover="this.style.color='var(--red)'" onmouseout="this.style.color='var(--text-muted)'">
          <i class="bi bi-trash3"></i>
        </button>
      </div>`).join('');

    if (!exact) {
      html += `
        <div style="display:flex;align-items:center;gap:6px;padding:7px 10px;cursor:pointer;
                    border-top:${filtered.length?'1px solid var(--border)':'none'};transition:background .1s"
             onmouseover="this.style.background='rgba(16,185,129,.08)'" onmouseout="this.style.background=''"
             onclick="_ctxCreateTag()">
          <i class="bi bi-plus" style="color:var(--green);font-size:14px"></i>
          <span style="font-size:12.5px">Crear <strong>${_ctxEsc(inp.value.trim())}</strong></span>
        </div>`;
    }

    dd.innerHTML  = html;
    dd.style.display = html ? 'block' : 'none';
  });

  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); _ctxCreateTag(); }
    if (e.key === 'Escape') dd.style.display = 'none';
  });
});

async function _ctxAddTag(tagId, tagName, tagColor) {
  const {txId, tx} = window._ctx;
  await fetch(`/api/transactions/${txId}/tags`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tag_id: tagId }),
  });
  tx.tags = [...(tx.tags || []), { id: tagId, name: tagName, color: tagColor }];
  _ctxRenderTags();
  document.getElementById('ctxTagInput').value = '';
  document.getElementById('ctxTagDropdown').style.display = 'none';
  if (window._ctx.reload) window._ctx.reload();
}

async function _ctxCreateTag() {
  const inp  = document.getElementById('ctxTagInput');
  const name = inp.value.trim();
  if (!name) return;
  const colors = ['#f9b233','#10b981','#f59e0b','#f43f5e','#06b6d4','#fb923c','#ec4899'];
  const color  = colors[Math.floor(Math.random() * colors.length)];
  const res = await fetch('/api/tags', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, color, account_id: window._ctx.accountId }),
  });
  if (!res.ok) { alert('Error al crear etiqueta'); return; }
  const tag = await res.json();
  window._ctx.tags.push(tag);
  await _ctxAddTag(tag.id, tag.name, tag.color);
}

async function _ctxDeleteTag(tagId, tagName) {
  if (!confirm(`¿Eliminar la etiqueta "${tagName}" de TODAS las transacciones?\nEsta acción no se puede deshacer.`)) return;
  await fetch(`/api/tags/${tagId}`, { method: 'DELETE' });
  window._ctx.tags = window._ctx.tags.filter(t => t.id !== tagId);
  if (window._ctx.tx) window._ctx.tx.tags = (window._ctx.tx.tags || []).filter(t => t.id !== tagId);
  _ctxRenderTags();
  document.getElementById('ctxTagDropdown').style.display = 'none';
  if (window._ctx.reload) window._ctx.reload();
}

// ── Close on outside click ─────────────────────────────────────────────────────
document.addEventListener('click', e => {
  const menu = document.getElementById('txCtxMenu');
  if (menu && !menu.contains(e.target)) menu.style.display = 'none';
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') _ctxClose();
});

// ── Helper utils ───────────────────────────────────────────────────────────────
function _ctxEsc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                         .replace(/'/g,'&#39;').replace(/"/g,'&quot;');
}
function _ctxFmt(v) {
  return new Intl.NumberFormat('es-ES', { style:'currency', currency:'EUR' }).format(v);
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick Facturas Modal
// ─────────────────────────────────────────────────────────────────────────────
let _qfModal    = null;
let _qfTxId     = null;
let _qfAccountId = null;

function openQfModal(txId, tx, accountId) {
  _qfTxId      = txId;
  _qfAccountId = accountId;

  const sign    = tx.is_income ? '+' : '−';
  const amtCls  = tx.is_income ? 'color:var(--green)' : 'color:var(--red)';
  document.getElementById('qfTitle').textContent    = tx.concepto || '—';
  document.getElementById('qfSubtitle').innerHTML   =
    `${tx.fecha} · <span style="${amtCls};font-weight:600">${sign}${_ctxFmt(Math.abs(tx.importe))}</span>`;
  document.getElementById('qfFullLink').href        = `/facturas?account=${accountId}`;
  document.getElementById('qfUploadWrap').style.display = 'none';

  if (!_qfModal && typeof bootstrap !== 'undefined')
    _qfModal = new bootstrap.Modal(document.getElementById('qfModal'));
  _qfModal?.show();

  _qfLoadFacturas();
}

async function _qfLoadFacturas() {
  if (!_qfTxId) return;
  document.getElementById('qfBody').innerHTML =
    '<div class="text-center py-4 text-muted small"><span class="spinner-border spinner-border-sm me-1"></span>Cargando…</div>';
  const res = await fetch(`/api/facturas?transaction_id=${_qfTxId}`);
  const facturas = await res.json();
  _qfRenderFacturas(facturas);
}

function _qfRenderFacturas(facturas) {
  const body = document.getElementById('qfBody');
  if (!facturas.length) {
    body.innerHTML = `
      <div class="text-center py-4 text-muted">
        <i class="bi bi-receipt" style="font-size:2rem"></i>
        <p class="small mt-2">Sin facturas adjuntas a esta transacción</p>
      </div>`;
    return;
  }
  body.innerHTML = facturas.map(f => {
    const ext  = (f.original_name || '').split('.').pop()?.toLowerCase();
    const icon = ext === 'pdf' ? 'bi-file-earmark-pdf text-accent-red'
               : ['jpg','jpeg','png','webp'].includes(ext) ? 'bi-file-earmark-image text-accent-blue'
               : 'bi-file-earmark';
    return `
    <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid var(--border)">
      <i class="bi ${icon}" style="font-size:20px;flex-shrink:0"></i>
      <div style="flex:1;min-width:0">
        <div style="font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${_ctxEsc(f.original_name)}</div>
        <div class="text-muted" style="font-size:11px">
          ${f.fecha_factura || ''}
          ${f.proveedor ? ' · ' + _ctxEsc(f.proveedor) : ''}
          ${f.importe != null ? ' · ' + _ctxFmt(f.importe) : ''}
        </div>
      </div>
      <div style="display:flex;gap:4px;flex-shrink:0">
        <a href="/api/facturas/${f.id}/file" target="_blank" class="icon-btn" title="Abrir">
          <i class="bi bi-box-arrow-up-right"></i>
        </a>
        <a href="/api/facturas/${f.id}/file" download="${_ctxEsc(f.original_name)}" class="icon-btn" title="Descargar">
          <i class="bi bi-download"></i>
        </a>
        <button class="icon-btn danger" onclick="_qfDeleteFactura(${f.id})" title="Eliminar">
          <i class="bi bi-trash3"></i>
        </button>
      </div>
    </div>`;
  }).join('');
}

function qfToggleUpload() {
  const w = document.getElementById('qfUploadWrap');
  if (!w) return;
  const showing = w.style.display !== 'none';
  w.style.display = showing ? 'none' : '';
  if (!showing) document.getElementById('qfFile')?.focus();
}

async function _qfDeleteFactura(facturaId) {
  if (!confirm('¿Eliminar esta factura?')) return;
  await fetch(`/api/facturas/${facturaId}`, { method: 'DELETE' });
  await _qfLoadFacturas();
  if (window._ctx.reload) window._ctx.reload();
}

async function qfUpload() {
  const file = document.getElementById('qfFile').files[0];
  if (!file) { alert('Selecciona un archivo'); return; }
  const btn = document.getElementById('qfUploadBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Subiendo...';
  const fd = new FormData();
  fd.append('file',           file);
  fd.append('transaction_id', _qfTxId);
  fd.append('account_id',     _qfAccountId || 1);
  fd.append('fecha_factura',  document.getElementById('qfFecha').value);
  fd.append('proveedor',      document.getElementById('qfProveedor').value);
  const res = await fetch('/api/facturas', { method: 'POST', body: fd });
  btn.disabled = false;
  btn.innerHTML = '<i class="bi bi-upload me-1"></i>Subir factura';
  if (res.ok) {
    document.getElementById('qfUploadWrap').style.display = 'none';
    document.getElementById('qfFile').value = '';
    await _qfLoadFacturas();
    if (window._ctx.reload) window._ctx.reload();
  } else {
    const e = await res.json();
    alert(e.error || 'Error al subir');
  }
}
