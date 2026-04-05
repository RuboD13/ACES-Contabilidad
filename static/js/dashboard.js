/* ─── Dashboard JS ─────────────────────────────────────────────────────────── */

// Chart.js global defaults
Chart.defaults.color          = '#64748b';
Chart.defaults.borderColor    = 'rgba(255,255,255,0.05)';
Chart.defaults.font.family    = 'Inter, system-ui, sans-serif';
Chart.defaults.font.size      = 12;

let chartIngresos = null;
let chartGastos   = null;
let chartEvolution = null;

// Active filters state
const filters = {
  tipo_tx:      '',
  date_from:    '',
  date_to:      '',
  min_importe:  '',
  max_importe:  '',
};

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  restoreFilters();
  loadDashboard();
  loadEvolution();
  loadDashTxs();
  setupFilterListeners();
  setupDashTxFilter();
  setupDashCtxMenu();
});

// ── Data loading ──────────────────────────────────────────────────────────────
let debounceTimer = null;
function scheduleReload() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(loadDashboard, 300);
}

async function loadDashboard() {
  const params = buildFilterParams();
  const res = await fetch(`/api/metrics/${PERIOD_ID}?${params}`);
  if (!res.ok) return;
  const data = await res.json();
  renderKPIs(data.kpis);
  renderIngresosChart(data.ingresos_por_fuente);
  renderGastosChart(data.gastos_por_categoria);
  renderReconciliation(data.reconciliation, data.reconciliation_companion);
  renderSubmetrics(data.submetrics);
  persistFilters();
}

async function loadEvolution() {
  const res = await fetch('/api/evolution');
  if (!res.ok) return;
  const evo = await res.json();
  if (evo.labels.length > 1) {
    document.getElementById('evolutionRow').style.removeProperty('display');
    renderEvolutionChart(evo);
  }
}

// ── KPI Cards ─────────────────────────────────────────────────────────────────
function renderKPIs(kpis) {
  animateValue('val-ingresos', kpis.ingresos_totales, true);
  animateValue('val-gastos',   kpis.gastos_totales,   true);
  animateValue('val-beneficio',kpis.beneficio_neto,   true);
  animateValue('val-ticket',   kpis.ticket_medio_ingresos, true);

  el('sub-beneficio').textContent = `Margen: ${fmt1(kpis.margen_pct)}%`;

  el('val-ops').textContent = kpis.total_operaciones;
  el('sub-ops').textContent = `${kpis.ingresos_count} ingresos · ${kpis.gastos_count} gastos`;

  // Gastos ratio bar
  const ratio = kpis.ingresos_totales > 0
    ? Math.min(kpis.gastos_totales / kpis.ingresos_totales * 100, 100)
    : 0;
  el('bar-gastos').style.width = ratio.toFixed(1) + '%';

  // Best source
  if (kpis.mejor_fuente) {
    el('val-best').textContent = formatEur(kpis.mejor_fuente.amount);
    el('sub-best').textContent = `${kpis.mejor_fuente.label} · ${fmt1(kpis.mejor_fuente.pct)}%`;
  }

  // Uncategorized alert
  const alertEl = el('alert-sincat');
  if (kpis.sin_categoria_count > 0) {
    alertEl.textContent = `${kpis.sin_categoria_count} sin categoría`;
    alertEl.classList.remove('d-none');
  } else {
    alertEl.classList.add('d-none');
  }

  // Trend badges (vs anterior)
  renderTrend('trend-ingresos',  kpis.vs_anterior?.ingresos_pct);
  renderTrend('trend-gastos',    kpis.vs_anterior?.gastos_pct,   true);
  renderTrend('trend-beneficio', kpis.vs_anterior?.beneficio_pct);
}

function renderTrend(id, pct, invert = false) {
  const el_ = el(id);
  if (pct == null) { el_.textContent = ''; el_.className = 'kpi-trend'; return; }
  const positive = invert ? pct < 0 : pct > 0;
  const icon = pct > 0 ? '↑' : '↓';
  el_.textContent = `${icon} ${Math.abs(pct)}%`;
  el_.className = `kpi-trend ${positive ? 'up' : 'down'}`;
}

// ── Ingresos Bar Chart ────────────────────────────────────────────────────────
function renderIngresosChart(data) {
  const isEmpty = !data || data.length === 0;
  toggleEmpty('emptyIngresos', 'chartIngresos', isEmpty);
  if (isEmpty) return;

  const labels  = data.map(d => d.label);
  const amounts = data.map(d => d.amount);
  const colors  = data.map(d => d.color);
  const pcts    = data.map(d => d.pct);

  const ctx = document.getElementById('chartIngresos').getContext('2d');
  if (chartIngresos) chartIngresos.destroy();

  chartIngresos = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Importe (€)',
        data: amounts,
        backgroundColor: colors.map(c => c + '33'),
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a1d27',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          callbacks: {
            label: (ctx) => {
              const d = data[ctx.dataIndex];
              return [
                ` ${formatEur(d.amount)}  (${d.pct}%)`,
                ` ${d.count} operaciones · ticket: ${formatEur(d.ticket_medio)}`,
              ];
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#64748b',
            callback: v => '€' + (v >= 1000 ? (v/1000).toFixed(1)+'k' : v),
          }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#94a3b8' }
        }
      },
      animation: { duration: 600, easing: 'easeOutQuart' }
    }
  });
}

// ── Gastos Doughnut ───────────────────────────────────────────────────────────
function renderGastosChart(data) {
  const isEmpty = !data || data.length === 0;
  toggleEmpty('emptyGastos', 'chartGastos', isEmpty);
  document.getElementById('doughnutLegend').innerHTML = '';
  document.getElementById('doughnutCenter').innerHTML = '';
  if (isEmpty) return;

  const labels  = data.map(d => d.label);
  const amounts = data.map(d => d.amount);
  const colors  = data.map(d => d.color);
  const total   = amounts.reduce((a,b) => a+b, 0);

  const ctx = document.getElementById('chartGastos').getContext('2d');
  if (chartGastos) chartGastos.destroy();

  chartGastos = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: amounts,
        backgroundColor: colors.map(c => c + '55'),
        borderColor: colors,
        borderWidth: 2,
        hoverBorderWidth: 3,
        hoverOffset: 6,
      }]
    },
    options: {
      cutout: '68%',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a1d27',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: (ctx) => {
              const d = data[ctx.dataIndex];
              return ` ${formatEur(d.amount)} (${d.pct}%)`;
            }
          }
        }
      },
      animation: { duration: 700, easing: 'easeOutQuart' }
    }
  });

  // Center label
  document.getElementById('doughnutCenter').innerHTML =
    `<div class="dc-val">${formatEur(total)}</div><div class="dc-label">Total gastos</div>`;

  // Legend
  const legend = document.getElementById('doughnutLegend');
  data.forEach(d => {
    legend.insertAdjacentHTML('beforeend', `
      <div class="doughnut-legend-item">
        <div class="dl-dot" style="background:${d.color}"></div>
        <span class="dl-label">${d.label}</span>
        <span class="dl-val">${formatEur(d.amount)}</span>
      </div>`);
  });
}

// ── Evolution Line Chart ──────────────────────────────────────────────────────
function renderEvolutionChart(evo) {
  const ctx = document.getElementById('chartEvolution').getContext('2d');
  if (chartEvolution) chartEvolution.destroy();

  const makeGradient = (color) => {
    const g = ctx.createLinearGradient(0, 0, 0, 200);
    g.addColorStop(0, color + '40');
    g.addColorStop(1, color + '00');
    return g;
  };

  chartEvolution = new Chart(ctx, {
    type: 'line',
    data: {
      labels: evo.labels,
      datasets: [
        {
          label: 'Ingresos',
          data: evo.ingresos,
          borderColor: '#10b981', backgroundColor: makeGradient('#10b981'),
          tension: 0.4, fill: true, pointRadius: 4, pointHoverRadius: 7,
          pointBackgroundColor: '#10b981', borderWidth: 2,
        },
        {
          label: 'Gastos',
          data: evo.gastos,
          borderColor: '#f43f5e', backgroundColor: makeGradient('#f43f5e'),
          tension: 0.4, fill: true, pointRadius: 4, pointHoverRadius: 7,
          pointBackgroundColor: '#f43f5e', borderWidth: 2,
        },
        {
          label: 'Beneficio',
          data: evo.beneficio,
          borderColor: '#f9b233', backgroundColor: makeGradient('#f9b233'),
          tension: 0.4, fill: true, pointRadius: 4, pointHoverRadius: 7,
          pointBackgroundColor: '#f9b233', borderWidth: 2, borderDash: [5,3],
        },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', usePointStyle: true, pointStyleWidth: 8, padding: 16 }
        },
        tooltip: {
          backgroundColor: '#1a1d27',
          borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, padding: 12,
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ${formatEur(ctx.raw)}` }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b' } },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', callback: v => '€'+(v>=1000?(v/1000).toFixed(0)+'k':v) }
        }
      },
      animation: { duration: 800 }
    }
  });
}

// ── Reconciliation ────────────────────────────────────────────────────────────
function renderReconciliation(recon, companion) {
  const section = el('reconciliationSection');
  const items = [recon, companion].filter(Boolean);
  if (!items.length) { section.innerHTML = ''; return; }

  section.innerHTML = `<div class="recon-grid">${items.map(renderReconCard).join('')}</div>`;
}

function renderReconCard(r) {
  const ok = r.is_reconciled;
  return `
  <div class="recon-card ${ok ? 'ok' : r.diferencia !== null ? 'error' : ''}">
    <div class="recon-title">
      <i class="bi bi-${r.tipo === 'banco' ? 'bank' : 'cash-coin'}"></i>
      Cuadre de ${r.tipo === 'banco' ? 'Banco' : 'Caja'}
    </div>
    <div class="recon-row">
      <span class="label">Saldo inicial</span>
      <span class="value">${formatEur(r.saldo_inicial)}</span>
    </div>
    <div class="recon-row">
      <span class="label">+ Ingresos</span>
      <span class="value" style="color:var(--green)">${formatEur(r.total_ingresos)}</span>
    </div>
    <div class="recon-row">
      <span class="label">− Gastos</span>
      <span class="value" style="color:var(--red)">${formatEur(r.total_gastos)}</span>
    </div>
    <div class="recon-row total">
      <span class="label">= Saldo calculado</span>
      <span class="value">${formatEur(r.saldo_calculado)}</span>
    </div>
    ${r.saldo_final_csv != null ? `
    <div class="recon-row">
      <span class="label">Saldo real (CSV/manual)</span>
      <span class="value">${formatEur(r.saldo_final_csv)}</span>
    </div>
    <div class="recon-row ${ok ? 'ok' : 'error'}">
      <span class="label">Diferencia</span>
      <span class="value">${formatEur(r.diferencia)}</span>
    </div>
    ` : ''}
    <div class="recon-status ${ok ? 'ok' : r.diferencia !== null ? 'error' : ''}">
      ${ok
        ? '<i class="bi bi-check-circle-fill"></i> Cuadre correcto'
        : r.diferencia !== null
          ? '<i class="bi bi-exclamation-triangle-fill"></i> Diferencia detectada'
          : '<i class="bi bi-info-circle"></i> Introduce saldo final para cuadrar'}
    </div>
  </div>`;
}

// ── Submetrics table ──────────────────────────────────────────────────────────
let allSubmetrics = [];
let subFilter = 'all';

function renderSubmetrics(data) {
  allSubmetrics = data;
  applySubFilter();
}

document.querySelectorAll('#submetricsFilter .seg-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#submetricsFilter .seg-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    subFilter = btn.dataset.value;
    applySubFilter();
  });
});

function applySubFilter() {
  const filtered = subFilter === 'all'
    ? allSubmetrics
    : allSubmetrics.filter(d => d.tipo === subFilter);

  const tbody = el('submetricsBody');
  if (!filtered.length) { tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Sin datos</td></tr>'; return; }

  tbody.innerHTML = filtered.map(d => {
    const isIncome = d.tipo === 'income';
    return `
    <tr>
      <td>
        <div class="d-flex align-items-center gap-2">
          <span class="cat-dot" style="background:${d.color}"></span>
          <span class="fw-500">${d.label}</span>
          <span class="badge-tipo ${isIncome ? 'badge-income' : 'badge-expense'}">${isIncome ? 'ingreso' : 'gasto'}</span>
        </div>
      </td>
      <td class="text-end fw-600" style="color:${isIncome ? 'var(--green)' : 'var(--red)'}">${formatEur(d.amount)}</td>
      <td class="text-end text-muted">${d.pct}%</td>
      <td class="text-end text-muted">${d.count}</td>
      <td class="text-end text-muted">${formatEur(d.ticket_medio)}</td>
      <td class="text-end">${renderTrendCell(d.vs_anterior_pct)}</td>
    </tr>`;
  }).join('');
}

function renderTrendCell(pct) {
  if (pct == null) return '<span class="trend-flat">—</span>';
  const icon = pct > 0 ? '↑' : '↓';
  return `<span class="${pct > 0 ? 'trend-up' : 'trend-down'}">${icon} ${Math.abs(pct)}%</span>`;
}

// ── Filter system ─────────────────────────────────────────────────────────────
function setupFilterListeners() {
  document.querySelectorAll('#tipoFilter .seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#tipoFilter .seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filters.tipo_tx = btn.dataset.value;
      updateChips();
      scheduleReload();
    });
  });

  ['filterDateFrom','filterDateTo','filterMinImp','filterMaxImp'].forEach(id => {
    el(id)?.addEventListener('input', e => {
      const map = {filterDateFrom:'date_from',filterDateTo:'date_to',filterMinImp:'min_importe',filterMaxImp:'max_importe'};
      filters[map[id]] = e.target.value;
      updateChips();
      scheduleReload();
    });
  });
}

function buildFilterParams() {
  const p = new URLSearchParams();
  if (filters.tipo_tx)    p.set('tipo_tx',    filters.tipo_tx);
  if (filters.date_from)  p.set('date_from',  filters.date_from);
  if (filters.date_to)    p.set('date_to',    filters.date_to);
  if (filters.min_importe) p.set('min_importe', filters.min_importe);
  if (filters.max_importe) p.set('max_importe', filters.max_importe);
  return p.toString();
}

function updateChips() {
  const chips = el('filterChips');
  chips.innerHTML = '';
  const labels = {
    tipo_tx: v => v === 'income' ? 'Solo ingresos' : 'Solo gastos',
    date_from: v => `Desde ${v}`,
    date_to:   v => `Hasta ${v}`,
    min_importe: v => `Mín. €${v}`,
    max_importe: v => `Máx. €${v}`,
  };
  let hasAny = false;
  Object.entries(filters).forEach(([k, v]) => {
    if (!v) return;
    hasAny = true;
    const chip = document.createElement('div');
    chip.className = 'filter-chip';
    chip.innerHTML = `<span>${labels[k](v)}</span><button onclick="removeFilter('${k}')">×</button>`;
    chips.appendChild(chip);
  });
  el('clearFiltersBtn')?.classList.toggle('d-none', !hasAny);
}

function removeFilter(key) {
  filters[key] = '';
  // Reset UI
  if (key === 'tipo_tx') {
    document.querySelectorAll('#tipoFilter .seg-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('#tipoFilter .seg-btn[data-value=""]').classList.add('active');
  }
  const inputMap = {date_from:'filterDateFrom',date_to:'filterDateTo',min_importe:'filterMinImp',max_importe:'filterMaxImp'};
  if (inputMap[key]) { const inp = el(inputMap[key]); if(inp) inp.value = ''; }
  updateChips();
  loadDashboard();
}

function clearFilters() {
  Object.keys(filters).forEach(k => filters[k] = '');
  document.querySelectorAll('#tipoFilter .seg-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('#tipoFilter .seg-btn[data-value=""]').classList.add('active');
  ['filterDateFrom','filterDateTo','filterMinImp','filterMaxImp'].forEach(id => {
    const inp = el(id); if(inp) inp.value = '';
  });
  updateChips();
  loadDashboard();
}

function persistFilters()  { sessionStorage.setItem(`filters_${PERIOD_ID}`, JSON.stringify(filters)); }
function restoreFilters()  {
  try {
    const saved = JSON.parse(sessionStorage.getItem(`filters_${PERIOD_ID}`) || '{}');
    Object.assign(filters, saved);
    if (filters.date_from) { const inp = el('filterDateFrom'); if(inp) inp.value = filters.date_from; }
    if (filters.date_to)   { const inp = el('filterDateTo');   if(inp) inp.value = filters.date_to; }
    if (filters.min_importe) { const inp = el('filterMinImp'); if(inp) inp.value = filters.min_importe; }
    if (filters.max_importe) { const inp = el('filterMaxImp'); if(inp) inp.value = filters.max_importe; }
    if (filters.tipo_tx) {
      document.querySelectorAll('#tipoFilter .seg-btn').forEach(b => b.classList.remove('active'));
      const btn = document.querySelector(`#tipoFilter .seg-btn[data-value="${filters.tipo_tx}"]`);
      if(btn) btn.classList.add('active');
    }
    updateChips();
  } catch(e) {}
}

// ── Dashboard transactions with multi-select ──────────────────────────────────
const TX_COLORS = {
  honorarios_gestion:'#10b981', busqueda_inquilinos:'#06b6d4',
  fee_garantia:'#f59e0b', fee_suministros:'#fb923c',
  fee_reparaciones:'#ec4899', renta_inquilinos:'#14b8a6',
  otros_ingresos:'#64748b',
  nominas:'#f43f5e', marketing:'#fb923c',
  software:'#fbbf24', gestoria:'#a78bfa',
  seguros:'#34d399', comisiones_banco:'#94a3b8',
  otros_gastos:'#6b7280', sin_categoria:'#4b5563',
};

let dashTxAll      = [];
let dashTxFiltered = [];
let dashSelected   = new Set();
const dashTxFilter = { search: '', tipo: '' };

async function loadDashTxs() {
  try {
    const res = await fetch(`/api/transactions/${PERIOD_ID}`);
    if (!res.ok) return;
    dashTxAll = await res.json();
    applyDashTxFilter();
  } catch (e) {
    el('dashTxLoading').style.display = 'none';
  }
}

function setupDashTxFilter() {
  el('dashTxSearch')?.addEventListener('input', e => {
    dashTxFilter.search = e.target.value.toLowerCase();
    showDashTxClearBtn();
    applyDashTxFilter();
  });
  document.querySelectorAll('#dashTxTipo .seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#dashTxTipo .seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      dashTxFilter.tipo = btn.dataset.value;
      showDashTxClearBtn();
      applyDashTxFilter();
    });
  });
}

function showDashTxClearBtn() {
  const hasFilter = dashTxFilter.search || dashTxFilter.tipo;
  const btn = el('dashTxClearBtn');
  if (btn) btn.style.display = hasFilter ? '' : 'none';
}

function applyDashTxFilter() {
  dashTxFiltered = dashTxAll.filter(tx => {
    if (dashTxFilter.tipo === 'income'   && tx.is_income !== 1) return false;
    if (dashTxFilter.tipo === 'expense'  && tx.is_income !== 0) return false;
    if (dashTxFilter.search) {
      const haystack = [
        tx.concepto, tx.category_label, tx.fecha,
        String(Math.abs(tx.importe))
      ].join(' ').toLowerCase();
      if (!haystack.includes(dashTxFilter.search)) return false;
    }
    return true;
  });
  renderDashTxTable(dashTxFiltered);
}

function dashClearTxFilter() {
  dashTxFilter.search = '';
  dashTxFilter.tipo   = '';
  const inp = el('dashTxSearch');
  if (inp) inp.value = '';
  document.querySelectorAll('#dashTxTipo .seg-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.value === '')
  );
  showDashTxClearBtn();
  applyDashTxFilter();
}

function renderDashTxTable(txs) {
  const loading = el('dashTxLoading');
  const empty   = el('dashTxEmpty');
  const wrap    = el('dashTxWrap');
  const count   = el('dashTxCount');

  loading.style.display = 'none';
  count.textContent = `${txs.length} transacciones`;

  if (!txs.length) {
    empty.classList.remove('d-none');
    return;
  }

  wrap.style.display = '';
  const tbody = el('dashTxBody');
  tbody.innerHTML = txs.map(tx => {
    const isIncome = tx.is_income === 1;
    const color    = TX_COLORS[tx.category_key] || '#64748b';
    const checked  = dashSelected.has(tx.id) ? 'checked' : '';
    return `
    <tr data-id="${tx.id}" class="${isIncome ? 'tx-income' : 'tx-expense'}">
      <td>
        <input type="checkbox" class="dash-tx-cb" ${checked}
               style="cursor:pointer;accent-color:var(--blue)"
               onchange="dashOnSelect(${tx.id}, this)"
               data-importe="${tx.importe}" data-income="${tx.is_income}">
      </td>
      <td class="text-muted" style="white-space:nowrap">${tx.fecha}</td>
      <td>
        <div class="tx-concepto">${escHtml(tx.concepto)}</div>
        ${tx.notes ? `<div class="tx-note-preview"><i class="bi bi-sticky me-1"></i>${escHtml(tx.notes)}</div>` : ''}
      </td>
      <td class="text-end tx-amount">${formatEur(tx.importe)}</td>
      <td class="text-end text-muted">${tx.saldo != null ? formatEur(tx.saldo) : '—'}</td>
      <td>
        <div class="d-flex align-items-center gap-1">
          <span class="cat-dot" style="background:${color}"></span>
          <span class="text-muted small">${escHtml(tx.category_label || 'Sin categoría')}</span>
        </div>
      </td>
    </tr>`;
  }).join('');
}

function dashOnSelect(id, cb) {
  if (cb.checked) dashSelected.add(id);
  else dashSelected.delete(id);
  dashUpdateMasterCb();
  dashUpdateToolbar();
}

function dashToggleAll(masterCb) {
  document.querySelectorAll('.dash-tx-cb').forEach(cb => {
    cb.checked = masterCb.checked;
    const id = parseInt(cb.closest('tr').dataset.id);
    if (masterCb.checked) dashSelected.add(id);
    else dashSelected.delete(id);
  });
  dashUpdateToolbar();
}

function dashSelectAll() {
  const masterCb = el('dashMasterCb');
  if (masterCb) { masterCb.checked = true; dashToggleAll(masterCb); }
}

function dashClearSelection() {
  dashSelected.clear();
  document.querySelectorAll('.dash-tx-cb').forEach(cb => cb.checked = false);
  const masterCb = el('dashMasterCb');
  if (masterCb) masterCb.checked = false;
  dashUpdateToolbar();
}

function dashUpdateMasterCb() {
  const masterCb = el('dashMasterCb');
  if (!masterCb) return;
  const all = document.querySelectorAll('.dash-tx-cb');
  const checked = [...all].filter(c => c.checked).length;
  masterCb.checked = checked > 0 && checked === all.length;
  masterCb.indeterminate = checked > 0 && checked < all.length;
}

function dashUpdateToolbar() {
  const toolbar = el('selectionToolbar');
  if (!toolbar) return;
  const n = dashSelected.size;

  if (n === 0) { toolbar.classList.add('d-none'); return; }
  toolbar.classList.remove('d-none');

  el('selCount').textContent = n;

  const selected  = dashTxAll.filter(t => dashSelected.has(t.id));
  const ingresos  = selected.filter(t => t.is_income === 1).reduce((s, t) => s + t.importe, 0);
  const gastos    = selected.filter(t => t.is_income === 0).reduce((s, t) => s + Math.abs(t.importe), 0);
  const neto      = ingresos - gastos;
  const ingCount  = selected.filter(t => t.is_income === 1).length;
  const ticket    = ingCount > 0 ? ingresos / ingCount : 0;

  el('selIngresos').textContent = formatEur(ingresos);
  el('selGastos').textContent   = formatEur(gastos);
  el('selNeto').textContent     = formatEur(neto);
  el('selNeto').style.color     = neto >= 0 ? 'var(--green)' : 'var(--red)';
  el('selTicket').textContent   = ingCount > 0 ? formatEur(ticket) : '—';

  // Saldo al inicio / al final (saldo column of first/last tx by fecha)
  const sorted = [...selected].sort((a, b) => a.fecha.localeCompare(b.fecha));
  const saldoInicio = sorted[0]?.saldo;
  const saldoFinal  = sorted[sorted.length - 1]?.saldo;
  el('selSaldoInicio').textContent = saldoInicio != null ? formatEur(saldoInicio) : '—';
  el('selSaldoFinal').textContent  = saldoFinal  != null ? formatEur(saldoFinal)  : '—';
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function el(id) { return document.getElementById(id); }

function formatEur(v) {
  if (v == null) return '—';
  return new Intl.NumberFormat('es-ES', { style:'currency', currency:'EUR', maximumFractionDigits:2 }).format(v);
}

function fmt1(v) { return (v ?? 0).toFixed(1); }

function toggleEmpty(emptyId, canvasId, isEmpty) {
  const emptyEl  = el(emptyId);
  const canvasEl = el(canvasId);
  if (emptyEl)  emptyEl.classList.toggle('d-none',  !isEmpty);
  if (canvasEl) canvasEl.classList.toggle('d-none',  isEmpty);
}

function animateValue(elId, target, isCurrency) {
  const el_ = el(elId);
  if (!el_) return;
  const start = 0;
  const duration = 700;
  const startTime = performance.now();
  const fmt = isCurrency ? formatEur : v => v.toFixed(0);

  function step(now) {
    const pct = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - pct, 3);
    el_.textContent = fmt(start + (target - start) * ease);
    if (pct < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── Context menu on dashboard transactions ─────────────────────────────────────
let _dashAllTags = [];

async function setupDashCtxMenu() {
  // Load tags for this account
  const res = await fetch(`/api/tags?account=${PERIOD_ACCOUNT_ID || PERIOD_ID}`);
  _dashAllTags = await res.json();

  window._ctx.reload = () => loadDashTxs();

  document.addEventListener('contextmenu', e => {
    const row = e.target.closest('#dashTxBody tr[data-id]');
    if (!row) return;
    e.preventDefault();
    const txId = +row.dataset.id;
    const tx   = dashTxAll?.find(t => t.id === txId);
    if (!tx) return;
    openCtxMenu(tx, PERIOD_ACCOUNT_ID || 1, _dashAllTags, e.clientX, e.clientY);
  });
}
