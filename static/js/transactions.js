/* ─── Transactions page JS ─────────────────────────────────────────────────── */

if (typeof RULES !== 'undefined') {

const COLORS = {
  honorarios_gestion:  '#10b981', busqueda_inquilinos: '#06b6d4',
  fee_garantia:        '#f59e0b', fee_suministros:     '#fb923c',
  fee_reparaciones:    '#ec4899', otros_ingresos:      '#64748b',
  nominas:             '#f43f5e', marketing:           '#fb923c',
  software:            '#fbbf24', gestoria:            '#a78bfa',
  seguros:             '#34d399', comisiones_banco:    '#94a3b8',
  otros_gastos:        '#6b7280', sin_categoria:       '#4b5563',
};

const RULE_MAP = {};
RULES.forEach(r => { RULE_MAP[r.key] = r; });

const CAT_OPTIONS = RULES.map(r =>
  `<option value="${r.key}" data-type="${r.tipo}">${escHtml(r.label)}</option>`
).join('');

let currentPeriodId = (typeof PERIOD_ID !== 'undefined') ? PERIOD_ID : null;
let allTxs          = [];
let allTags         = [];
let tagFilter       = '';
let currentFilters  = {};
let debounce        = null;
let txDetailModal   = null;
let facturaModal    = null;
let currentTxId     = null;

document.addEventListener('DOMContentLoaded', () => {
  loadPeriodList();
  setupFilters();
  loadTags();
  setupContextMenu();
  setupDragDrop();
  restorePflCollapse();

  // If a period was in the URL, show the tx section immediately
  if (currentPeriodId) {
    loadTransactions();
    document.getElementById('txSection').style.display = '';
  }

  // Bootstrap-dependent — lazy to avoid blocking data load if CDN unavailable
  if (typeof bootstrap !== 'undefined') {
    txDetailModal = new bootstrap.Modal(document.getElementById('txDetailModal'));
    facturaModal  = new bootstrap.Modal(document.getElementById('facturaModal'));
  }
});

// ── Period list ────────────────────────────────────────────────────────────────
async function loadPeriodList() {
  const body  = document.getElementById('periodListBody');
  const count = document.getElementById('periodListCount');

  try {
    const res     = await fetch(`/api/periods/history?account=${ACCOUNT_ID}`);
    const periods = await res.json();

    count.textContent = `${periods.length} archivo${periods.length !== 1 ? 's' : ''}`;

    if (!periods.length) {
      body.innerHTML = `
        <div class="text-center py-5 text-muted">
          <i class="bi bi-inbox" style="font-size:2rem"></i>
          <p class="mt-2">No hay archivos importados aún.</p>
          <a href="/upload?account=${ACCOUNT_ID}" class="btn-xs-ghost mt-1">
            <i class="bi bi-plus me-1"></i>Importar primer archivo
          </a>
        </div>`;
      return;
    }

    body.innerHTML = periods.map(p => {
      const isActive = p.id === currentPeriodId;
      const neto     = (p.ingresos || 0) - (p.gastos || 0);
      return `
      <div class="pfl-item ${isActive ? 'active' : ''}" id="pfl-${p.id}"
           data-pid="${p.id}"
           data-name="${escHtml(p.name)}"
           data-from="${escHtml(p.date_from)}"
           data-to="${escHtml(p.date_to)}"
           data-count="${p.tx_count || 0}"
           data-tipo="${escHtml(p.tipo)}">
        <div class="pfl-left">
          <div class="pfl-icon">
            <i class="bi bi-${p.tipo === 'banco' ? 'bank' : 'cash-coin'}"></i>
          </div>
          <div class="min-w-0">
            <div class="pfl-name">${escHtml(p.name)}</div>
            <div class="pfl-meta">
              ${escHtml(p.date_from)} → ${escHtml(p.date_to)}
              ${p.csv_filename ? `<span class="ms-2 text-accent-blue">${escHtml(p.csv_filename)}</span>` : ''}
            </div>
          </div>
        </div>
        <div class="pfl-right">
          <div class="pfl-stats-mini">
            <span class="text-accent-green">${fmtEur(p.ingresos || 0)}</span>
            <span class="text-accent-red">−${fmtEur(p.gastos || 0)}</span>
            <span class="${neto >= 0 ? 'text-accent-green' : 'text-accent-red'} fw-600">${fmtEur(neto)}</span>
          </div>
          <span class="pfl-count">${p.tx_count || 0} tx</span>
          <span class="badge-tipo badge-${p.tipo}">${p.tipo}</span>
          <button class="pfl-delete-btn" title="Eliminar período" data-delete-pid="${p.id}" data-delete-name="${escHtml(p.name)}">
            <i class="bi bi-trash"></i>
          </button>
          <i class="bi bi-chevron-right pfl-arrow ${isActive ? 'rot' : ''}"></i>
        </div>
      </div>`;
    }).join('');

    // Event delegation for period clicks and delete buttons
    body.onclick = e => {
      const delBtn = e.target.closest('[data-delete-pid]');
      if (delBtn) {
        e.stopPropagation();
        deletePeriod(+delBtn.dataset.deletePid, delBtn.dataset.deleteName);
        return;
      }
      const item = e.target.closest('.pfl-item[data-pid]');
      if (item) {
        selectPeriod(+item.dataset.pid, item.dataset.name, item.dataset.from, item.dataset.to, +item.dataset.count, item.dataset.tipo);
      }
    };

    // If active period, fill in the tx section header
    if (currentPeriodId) {
      const active = periods.find(p => p.id === currentPeriodId);
      if (active) updateTxSectionHeader(active.name, active.date_from, active.date_to, active.tx_count || 0, active.tipo);
    }

  } catch (e) {
    body.innerHTML = '<div class="text-center py-4 text-muted small">Error al cargar los períodos.</div>';
  }
}

function selectPeriod(id, name, dateFrom, dateTo, txCount, tipo) {
  // Highlight
  document.querySelectorAll('.pfl-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.pfl-arrow').forEach(el => el.classList.remove('rot'));
  const item = document.getElementById(`pfl-${id}`);
  if (item) {
    item.classList.add('active');
    item.querySelector('.pfl-arrow')?.classList.add('rot');
  }

  currentPeriodId = id;

  // Show tx section
  document.getElementById('txSection').style.display = '';
  updateTxSectionHeader(name, dateFrom, dateTo, txCount, tipo);

  // Update URL without navigation
  const url = new URL(window.location);
  url.searchParams.set('period', id);
  window.history.replaceState({}, '', url);

  // Reset filters and load
  clearFiltersState();
  loadTransactions();
}

function updateTxSectionHeader(name, dateFrom, dateTo, txCount, tipo) {
  const titleEl = document.getElementById('txSectionTitle');
  const metaEl  = document.getElementById('txSectionMeta');
  if (titleEl) {
    const icon = tipo === 'banco' ? 'bank' : 'cash-coin';
    titleEl.innerHTML = `<i class="bi bi-${icon} me-2"></i>${escHtml(name)}`;
  }
  if (metaEl) metaEl.textContent = `${dateFrom} → ${dateTo} · ${txCount} transacciones`;
}

function closeTxSection() {
  document.getElementById('txSection').style.display = 'none';
  document.querySelectorAll('.pfl-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.pfl-arrow').forEach(el => el.classList.remove('rot'));
  currentPeriodId = null;
  document.getElementById('txCount').textContent = '';
  const url = new URL(window.location);
  url.searchParams.delete('period');
  window.history.replaceState({}, '', url);
}

async function deletePeriod(periodId, name) {
  if (!confirm(`¿Eliminar el período "${name}" y todas sus transacciones?`)) return;
  const res = await fetch(`/api/periods/${periodId}`, { method: 'DELETE' });
  if (res.ok) {
    if (currentPeriodId === periodId) {
      closeTxSection();
    }
    loadPeriodList();
  } else {
    const err = await res.json();
    alert(err.error || 'Error al eliminar');
  }
}

// ── Tags ───────────────────────────────────────────────────────────────────────
async function loadTags() {
  const res = await fetch(`/api/tags?account=${ACCOUNT_ID}`);
  allTags = await res.json();
  const sel = document.getElementById('tagFilter');
  if (sel) {
    allTags.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      sel.appendChild(opt);
    });
  }
}

// ── Data ───────────────────────────────────────────────────────────────────────
async function loadTransactions() {
  if (!currentPeriodId) return;
  showLoading(true);
  const params = buildParams();
  const res = await fetch(`/api/transactions/${currentPeriodId}?${params}`);
  let txs = await res.json();

  if (tagFilter) {
    const tid = parseInt(tagFilter);
    txs = txs.filter(tx => tx.tags && tx.tags.some(t => t.id === tid));
  }

  allTxs = txs;
  renderTable(allTxs);
  showLoading(false);
}

function scheduleReload() {
  clearTimeout(debounce);
  debounce = setTimeout(loadTransactions, 280);
}

// ── Render ─────────────────────────────────────────────────────────────────────
function renderTable(txs) {
  const tbody = document.getElementById('txBody');
  const count = document.getElementById('txCount');
  const empty = document.getElementById('emptyState');
  const wrap  = document.getElementById('tableWrap');

  count.textContent = `${txs.length} transacciones`;

  if (!txs.length) {
    wrap.style.display = 'none';
    empty.classList.remove('d-none');
    return;
  }
  empty.classList.add('d-none');
  wrap.style.display = '';
  tbody.innerHTML = txs.map(tx => renderRow(tx)).join('');
}

function renderRow(tx) {
  const isIncome  = tx.is_income === 1;
  const isUncat   = tx.category_key === 'sin_categoria';
  const color     = COLORS[tx.category_key] || '#64748b';
  const catLabel  = tx.category_label || 'Sin categoría';
  const rowClass  = `${isIncome ? 'tx-income' : 'tx-expense'} ${isUncat ? 'tx-uncat' : ''}`;
  const confClass = tx.confidence < 1 && !tx.is_manual_override ? 'conf-low' : '';

  const tagsHtml = (tx.tags || []).map(t =>
    `<span class="tx-tag" style="background:${t.color}22;color:${t.color};border-color:${t.color}44"
           onclick="event.stopPropagation()">${escHtml(t.name)}</span>`
  ).join('');

  const noteHtml = tx.notes
    ? `<div class="tx-note-preview"><i class="bi bi-sticky me-1"></i>${escHtml(tx.notes)}</div>`
    : '';

  const facturaIcon = tx.factura_count > 0
    ? `<span class="factura-count-badge" title="${tx.factura_count} factura(s) adjunta(s)">
         <i class="bi bi-paperclip"></i>${tx.factura_count}
       </span>`
    : `<button class="icon-btn" onclick="openFacturaModal(${tx.id})" title="Adjuntar factura">
         <i class="bi bi-paperclip text-muted"></i>
       </button>`;

  return `
  <tr class="${rowClass}" data-id="${tx.id}">
    <td class="text-muted" style="white-space:nowrap">${tx.fecha}</td>
    <td>
      <div class="tx-concepto-wrap">
        <span class="tx-concepto ${confClass}">${escHtml(tx.concepto)}</span>
        ${tagsHtml}
      </div>
      ${noteHtml}
    </td>
    <td class="text-end tx-amount">${fmtEur(tx.importe)}</td>
    <td class="text-end text-muted">${tx.saldo != null ? fmtEur(tx.saldo) : '—'}</td>
    <td>
      <div class="d-flex align-items-center gap-1">
        <span class="cat-dot" style="background:${color}"></span>
        <select class="cat-select" onchange="updateCategory(${tx.id}, this.value, this)"
                data-original="${tx.category_key}">
          ${CAT_OPTIONS.replace(`value="${tx.category_key}"`, `value="${tx.category_key}" selected`)}
        </select>
        ${tx.is_manual_override ? '<i class="bi bi-pencil-fill" style="font-size:10px;color:var(--text-muted)" title="Editado manualmente"></i>' : ''}
      </div>
    </td>
    <td class="text-center">${facturaIcon}</td>
    <td>
      <div class="d-flex gap-1">
        <button class="icon-btn" onclick="openTxDetail(${tx.id})" title="Editar detalle, notas y etiquetas">
          <i class="bi bi-three-dots"></i>
        </button>
        <button class="icon-btn danger" onclick="deleteTx(${tx.id})" title="Eliminar">
          <i class="bi bi-trash"></i>
        </button>
      </div>
    </td>
  </tr>`;
}

// ── Transaction detail modal ────────────────────────────────────────────────────
function _getTxModal() {
  if (!txDetailModal && typeof bootstrap !== 'undefined')
    txDetailModal = new bootstrap.Modal(document.getElementById('txDetailModal'));
  return txDetailModal;
}
function _getFacModal() {
  if (!facturaModal && typeof bootstrap !== 'undefined')
    facturaModal = new bootstrap.Modal(document.getElementById('facturaModal'));
  return facturaModal;
}

async function openTxDetail(txId) {
  currentTxId = txId;
  const tx = allTxs.find(t => t.id === txId);
  if (!tx) return;

  document.getElementById('txDetailTitle').textContent = tx.concepto;
  document.getElementById('txDetailMeta').textContent =
    `${tx.fecha}  ·  ${fmtEur(tx.importe)}  ·  ${tx.category_label || 'Sin categoría'}`;

  const tagOptions = allTags.map(t => {
    const sel = (tx.tags || []).some(tg => tg.id === t.id);
    return `<label class="tag-toggle-option ${sel ? 'selected' : ''}"
                   data-tag-id="${t.id}"
                   style="--tag-color:${t.color}"
                   onclick="toggleTxTag(${txId}, ${t.id}, this)">
              <span class="tag-toggle-dot" style="background:${t.color}"></span>
              ${escHtml(t.name)}
            </label>`;
  }).join('');

  document.getElementById('txDetailBody').innerHTML = `
    <div class="mb-3">
      <label class="form-label-custom d-flex align-items-center gap-2">
        Notas
        <span class="info-tooltip" data-tip="Añade una nota interna a esta transacción.">
          <i class="bi bi-info-circle text-muted"></i>
        </span>
      </label>
      <textarea class="form-control-custom" id="detailNotes" rows="3"
                placeholder="Añade contexto, referencias, observaciones...">${escHtml(tx.notes || '')}</textarea>
    </div>
    <div class="mb-3">
      <label class="form-label-custom d-flex align-items-center gap-2">
        Etiquetas
        <span class="info-tooltip" data-tip="Las etiquetas son marcas personalizadas. Puedes gestionarlas desde la sección Reglas.">
          <i class="bi bi-info-circle text-muted"></i>
        </span>
      </label>
      ${allTags.length
        ? `<div class="tag-toggle-grid" id="tagToggleGrid">${tagOptions}</div>`
        : `<div class="text-muted small">No hay etiquetas. Ve a <a href="/rules" class="text-accent-blue">Reglas</a> para crearlas.</div>`}
    </div>
    <div class="mb-3">
      <label class="form-label-custom">Facturas adjuntas</label>
      <div id="detailFacturas" class="text-muted small">Cargando...</div>
    </div>
    ${_buildRawDataSection(tx)}
  `;

  loadTxFacturas(txId);
  _getTxModal()?.show();
}

async function loadTxFacturas(txId) {
  const res = await fetch(`/api/facturas?transaction_id=${txId}&account=${ACCOUNT_ID}`);
  const facturas = await res.json();
  const el = document.getElementById('detailFacturas');
  if (!el) return;

  if (!facturas.length) {
    el.innerHTML = `<span>Sin facturas adjuntas.</span>
      <button class="btn-xs-ghost ms-2" onclick="openFacturaModal(${txId})">
        <i class="bi bi-plus me-1"></i>Adjuntar factura
      </button>`;
    return;
  }

  el.innerHTML = facturas.map(f => `
    <div class="factura-inline-item">
      <i class="bi bi-file-earmark-pdf text-accent-red me-1"></i>
      <a href="/api/facturas/${f.id}/file" target="_blank" class="text-accent-blue">${escHtml(f.original_name)}</a>
      ${f.proveedor ? `<span class="text-muted ms-2">· ${escHtml(f.proveedor)}</span>` : ''}
      ${f.importe != null ? `<span class="text-muted ms-2">· ${fmtEur(f.importe)}</span>` : ''}
      <button class="icon-btn danger ms-auto" onclick="deleteFacturaInline(${f.id}, ${txId})" title="Eliminar">
        <i class="bi bi-trash" style="font-size:11px"></i>
      </button>
    </div>
  `).join('') + `
    <button class="btn-xs-ghost mt-2" onclick="openFacturaModal(${txId})">
      <i class="bi bi-plus me-1"></i>Adjuntar otra factura
    </button>`;
}

async function deleteFacturaInline(facturaId, txId) {
  if (!confirm('¿Eliminar esta factura?')) return;
  await fetch(`/api/facturas/${facturaId}`, { method: 'DELETE' });
  loadTxFacturas(txId);
  loadTransactions();
}

async function saveTxDetail() {
  if (!currentTxId) return;
  const notes = document.getElementById('detailNotes')?.value || '';
  await fetch(`/api/transactions/${currentTxId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });
  _getTxModal()?.hide();
  loadTransactions();
}

async function toggleTxTag(txId, tagId, el) {
  const isSelected = el.classList.contains('selected');
  if (isSelected) {
    await fetch(`/api/transactions/${txId}/tags/${tagId}`, { method: 'DELETE' });
    el.classList.remove('selected');
  } else {
    await fetch(`/api/transactions/${txId}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag_id: tagId }),
    });
    el.classList.add('selected');
  }
  loadTransactions();
}

// ── Factura modal ───────────────────────────────────────────────────────────────
function openFacturaModal(txId) {
  currentTxId = txId;
  document.getElementById('facturaTxId').value = txId;
  ['facturaFile','facturaFecha','facturaNumero','facturaProveedor','facturaImporte','facturaNotas']
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  _getFacModal()?.show();
}

async function uploadFactura() {
  const txId = document.getElementById('facturaTxId').value;
  const file = document.getElementById('facturaFile').files[0];
  if (!file) { alert('Selecciona un archivo'); return; }

  const btn = document.getElementById('facturaSubmitBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Subiendo...';

  const fd = new FormData();
  fd.append('file', file);
  fd.append('transaction_id', txId);
  fd.append('account_id', ACCOUNT_ID);
  fd.append('fecha_factura',  document.getElementById('facturaFecha').value);
  fd.append('numero_factura', document.getElementById('facturaNumero').value);
  fd.append('proveedor',      document.getElementById('facturaProveedor').value);
  fd.append('importe',        document.getElementById('facturaImporte').value);
  fd.append('notes',          document.getElementById('facturaNotas').value);

  const res = await fetch('/api/facturas', { method: 'POST', body: fd });
  btn.disabled = false;
  btn.innerHTML = '<i class="bi bi-upload me-1"></i>Adjuntar';

  if (res.ok) {
    _getFacModal()?.hide();
    loadTransactions();
    alert('Factura adjuntada correctamente.');
  } else {
    const err = await res.json();
    alert(err.error || 'Error al subir');
  }
}

// ── Inline edit ────────────────────────────────────────────────────────────────
async function updateCategory(txId, newKey, selectEl) {
  const row = selectEl.closest('tr');
  try {
    const res = await fetch(`/api/transactions/${txId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category_key: newKey }),
    });
    if (!res.ok) throw new Error();
    const dot = row.querySelector('.cat-dot');
    if (dot) dot.style.background = COLORS[newKey] || '#64748b';
    row.classList.toggle('tx-uncat', newKey === 'sin_categoria');
    if (!row.querySelector('.bi-pencil-fill')) {
      selectEl.insertAdjacentHTML('afterend',
        '<i class="bi bi-pencil-fill" style="font-size:10px;color:var(--text-muted)" title="Editado manualmente"></i>');
    }
    selectEl.dataset.original = newKey;
    const tx = allTxs.find(t => t.id === txId);
    if (tx) { tx.category_key = newKey; tx.is_manual_override = 1; }
  } catch {
    selectEl.value = selectEl.dataset.original;
    alert('Error al actualizar la categoría.');
  }
}

async function deleteTx(txId) {
  if (!confirm('¿Eliminar esta transacción?')) return;
  await fetch(`/api/transactions/${txId}`, { method: 'DELETE' });
  const row = document.querySelector(`tr[data-id="${txId}"]`);
  if (row) row.remove();
  const count = document.getElementById('txCount');
  const n = parseInt(count.textContent) - 1;
  count.textContent = `${n} transacciones`;
}

// ── Filters ────────────────────────────────────────────────────────────────────
function setupFilters() {
  document.getElementById('searchInput')?.addEventListener('input', e => {
    currentFilters.search = e.target.value;
    toggleClearBtn(); scheduleReload();
  });

  document.querySelectorAll('#tipoFilter .seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#tipoFilter .seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilters.tipo_tx = btn.dataset.value;
      toggleClearBtn(); loadTransactions();
    });
  });

  document.getElementById('categoryFilter')?.addEventListener('change', e => {
    currentFilters.categories = e.target.value;
    toggleClearBtn(); loadTransactions();
  });

  document.getElementById('tagFilter')?.addEventListener('change', e => {
    tagFilter = e.target.value;
    toggleClearBtn(); loadTransactions();
  });

  document.getElementById('uncatOnly')?.addEventListener('change', e => {
    currentFilters.uncat_only = e.target.checked ? '1' : '';
    toggleClearBtn(); loadTransactions();
  });

  document.getElementById('dateFrom')?.addEventListener('change', e => {
    currentFilters.date_from = e.target.value;
    toggleClearBtn(); loadTransactions();
  });

  document.getElementById('dateTo')?.addEventListener('change', e => {
    currentFilters.date_to = e.target.value;
    toggleClearBtn(); loadTransactions();
  });
}

function buildParams() {
  const p = new URLSearchParams();
  if (currentFilters.tipo_tx)    p.set('tipo_tx',    currentFilters.tipo_tx);
  if (currentFilters.search)     p.set('search',     currentFilters.search);
  if (currentFilters.categories) p.set('categories', currentFilters.categories);
  if (currentFilters.uncat_only) p.set('uncat_only', currentFilters.uncat_only);
  if (currentFilters.date_from)  p.set('date_from',  currentFilters.date_from);
  if (currentFilters.date_to)    p.set('date_to',    currentFilters.date_to);
  return p.toString();
}

function clearFiltersState() {
  currentFilters = {};
  tagFilter = '';
  const ids = ['searchInput','dateFrom','dateTo'];
  ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  document.querySelectorAll('#tipoFilter .seg-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('#tipoFilter .seg-btn[data-value=""]')?.classList.add('active');
  const catF = document.getElementById('categoryFilter');
  if (catF) catF.value = '';
  const tagF = document.getElementById('tagFilter');
  if (tagF) tagF.value = '';
  const unc = document.getElementById('uncatOnly');
  if (unc) unc.checked = false;
  toggleClearBtn();
}

function clearFilters() {
  clearFiltersState();
  loadTransactions();
}

function toggleClearBtn() {
  const hasAny = Object.values(currentFilters).some(v => v) || !!tagFilter;
  const btn = document.getElementById('clearBtn');
  if (btn) btn.style.display = hasAny ? '' : 'none';
}

// ── UI states ──────────────────────────────────────────────────────────────────
function showLoading(show) {
  document.getElementById('loadingState').style.display = show ? '' : 'none';
  if (show) {
    document.getElementById('tableWrap').style.display = 'none';
    document.getElementById('emptyState').classList.add('d-none');
  }
}

// ── Raw data section for detail modal ─────────────────────────────────────────
function _buildRawDataSection(tx) {
  let parsed = null;
  if (tx.raw_data) {
    try { parsed = typeof tx.raw_data === 'string' ? JSON.parse(tx.raw_data) : tx.raw_data; }
    catch(e) { parsed = null; }
  }
  if (!parsed || !Object.keys(parsed).length) return '';
  const rows = Object.entries(parsed).map(([k,v]) =>
    `<tr><td>${escHtml(k)}</td><td>${escHtml(v)}</td></tr>`
  ).join('');
  return `
    <div>
      <label class="form-label-custom" style="cursor:pointer" onclick="this.nextElementSibling.classList.toggle('d-none')">
        <i class="bi bi-table me-1"></i>Datos originales del archivo
        <i class="bi bi-chevron-down ms-1" style="font-size:10px"></i>
      </label>
      <div class="d-none" style="margin-top:6px;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px 10px;max-height:180px;overflow-y:auto">
        <table class="raw-data-table"><tbody>${rows}</tbody></table>
      </div>
    </div>`;
}

// ── Utilities ──────────────────────────────────────────────────────────────────
function fmtEur(v) {
  return new Intl.NumberFormat('es-ES', { style:'currency', currency:'EUR' }).format(v);
}
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Collapsible period list ────────────────────────────────────────────────────
function togglePflCollapse() {
  const collapse = document.getElementById('periodListCollapse');
  const icon     = document.getElementById('pflCollapseIcon');
  const isHidden = collapse.style.display === 'none';
  collapse.style.display = isHidden ? '' : 'none';
  icon.className = isHidden ? 'bi bi-chevron-up' : 'bi bi-chevron-down';
  localStorage.setItem('pfl_collapsed', isHidden ? '0' : '1');
}

function restorePflCollapse() {
  if (localStorage.getItem('pfl_collapsed') === '1') {
    const collapse = document.getElementById('periodListCollapse');
    const icon     = document.getElementById('pflCollapseIcon');
    if (collapse) collapse.style.display = 'none';
    if (icon)     icon.className = 'bi bi-chevron-down';
  }
}

// ── Right-click context menu ───────────────────────────────────────────────────
function setupContextMenu() {
  // Use shared context menu from ctx_menu.js
  window._ctx.reload = () => loadTransactions();

  document.addEventListener('contextmenu', e => {
    const row = e.target.closest('#txBody tr[data-id]');
    if (!row) { _ctxClose(); return; }
    e.preventDefault();
    const txId = +row.dataset.id;
    const tx   = allTxs.find(t => t.id === txId);
    if (!tx) return;
    openCtxMenu(tx, ACCOUNT_ID, allTags, e.clientX, e.clientY);
  });
}

// ── Drag & drop to attach factura ──────────────────────────────────────────────
function setupDragDrop() {
  const section = document.getElementById('txSection');
  const overlay = document.getElementById('dragOverlay');
  if (!section || !overlay) return;

  let dragTarget = null;

  document.addEventListener('dragenter', e => {
    if (e.dataTransfer.types.includes('Files')) {
      dragTarget = e.target;
      overlay.style.display = 'flex';
    }
  });

  document.addEventListener('dragleave', e => {
    if (e.target === dragTarget || !document.body.contains(e.relatedTarget)) {
      overlay.style.display = 'none';
    }
  });

  document.addEventListener('dragover', e => {
    if (e.dataTransfer.types.includes('Files')) e.preventDefault();
  });

  document.addEventListener('drop', e => {
    overlay.style.display = 'none';
    if (!e.dataTransfer.files.length) return;
    e.preventDefault();

    const file = e.dataTransfer.files[0];

    // Find which tx row (if any) was under the cursor
    const row = e.target.closest('#txBody tr[data-id]');
    const txId = row ? +row.dataset.id : null;

    // Confirm + open factura modal
    const txInfo = txId ? allTxs.find(t => t.id === txId) : null;
    const msg = txInfo
      ? `¿Adjuntar "${file.name}" a la transacción "${txInfo.concepto}"?`
      : `¿Adjuntar "${file.name}" como factura suelta?`;

    if (!confirm(msg)) return;

    if (txId) openFacturaModal(txId);
    else openFacturaModal(null);

    // Pre-fill the file input after modal opens
    setTimeout(() => {
      const fi = document.getElementById('facturaFile');
      if (!fi) return;
      const dt = new DataTransfer();
      dt.items.add(file);
      fi.files = dt.files;
      // Show filename hint
      const hint = fi.closest('.mb-3')?.querySelector('.drop-hint');
      if (!hint) {
        const span = document.createElement('div');
        span.className = 'text-accent-green small mt-1';
        span.textContent = `📎 ${file.name}`;
        fi.insertAdjacentElement('afterend', span);
      }
    }, 150);
  });
}

// Tooltip init (optional — requires Bootstrap JS)
document.addEventListener('DOMContentLoaded', () => {
  if (typeof bootstrap === 'undefined') return;
  document.querySelectorAll('.info-tooltip[data-tip]').forEach(el => {
    el.setAttribute('title', el.dataset.tip);
    new bootstrap.Tooltip(el, { placement: 'top', trigger: 'hover' });
  });
});

// Expose async functions to global scope (async fn declarations inside if-blocks are block-scoped in Chrome)
window.openTxDetail       = openTxDetail;
window.saveTxDetail       = saveTxDetail;
window.loadTxFacturas     = loadTxFacturas;
window.deleteFacturaInline= deleteFacturaInline;
window.toggleTxTag        = toggleTxTag;
window.updateCategory     = updateCategory;
window.uploadFactura      = uploadFactura;
window.deleteTx           = deleteTx;
window.deletePeriod       = deletePeriod;
window.loadTransactions   = loadTransactions;

} // end if RULES
