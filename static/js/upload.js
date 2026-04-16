/* ─── Upload page JS ───────────────────────────────────────────────────────── */

const dropZone   = document.getElementById('dropZone');
const fileInput  = document.getElementById('csv_file');
const submitBtn  = document.getElementById('submitBtn');

// Detected periods state (array of {name, date_from, date_to, saldo_inicial})
let detectedPeriods = [];

// ── Drag & drop ───────────────────────────────────────────────────────────────
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) { fileInput.files = e.dataTransfer.files; handleFile(file); }
});
fileInput.addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

// ── Tipo toggle ───────────────────────────────────────────────────────────────
document.querySelectorAll('input[name="_tipo_ui"]').forEach(r =>
  r.addEventListener('change', () => document.getElementById('tipoHidden').value = r.value)
);

// ── File handling ─────────────────────────────────────────────────────────────
async function handleFile(file) {
  const valid = /\.(csv|txt|xls|xlsx)$/i.test(file.name);
  setDropState(valid ? 'loading' : 'error', file.name);

  if (!valid) {
    showError('Formato no válido. Solo se aceptan archivos .csv, .txt, .xls o .xlsx');
    return;
  }

  hideError();
  el('parsingSpinner').classList.remove('d-none');
  el('previewSection').classList.add('d-none');

  const form = new FormData();
  form.append('csv_file', file);

  try {
    const res  = await fetch('/upload/preview', { method: 'POST', body: form });
    const data = await res.json();

    el('parsingSpinner').classList.add('d-none');

    if (data.error) { showError(data.error); setDropState('error', file.name); return; }

    setDropState('ok', file.name);
    // Auto-select tipo based on server suggestion
    if (data.tipo_sugerido) {
      document.querySelectorAll('input[name="_tipo_ui"]').forEach(r => {
        r.checked = (r.value === data.tipo_sugerido);
      });
      document.getElementById('tipoHidden').value = data.tipo_sugerido;
      const hint = document.getElementById('tipoAutoHint');
      if (hint) {
        const label = data.tipo_sugerido === 'caja' ? 'Caja (detectado automáticamente)' : 'Banco (detectado automáticamente)';
        hint.textContent = label;
        hint.classList.remove('d-none');
      }
    }
    renderPreview(data);
  } catch (e) {
    el('parsingSpinner').classList.add('d-none');
    showError('Error de red al procesar el archivo.');
    setDropState('error', file.name);
  }
}

// ── Render preview ────────────────────────────────────────────────────────────
function renderPreview(data) {
  detectedPeriods = data.periods.map(p => ({
    name:          p.name,
    date_from:     p.date_from,
    date_to:       p.date_to,
    saldo_inicial: p.saldo_inicial != null ? p.saldo_inicial : null,
    selected:      true,   // all selected by default
    _count:        p.transaction_count,
    _ingresos:     p.ingresos,
    _gastos:       p.gastos,
  }));

  // Summary
  el('previewSummary').textContent =
    `${data.total} transacciones · ${data.date_from} → ${data.date_to}`;

  // Period cards
  renderPeriodCards();

  // Preview table
  const tbody = el('previewBody');
  tbody.innerHTML = data.rows.map(r => `
    <tr class="${r.importe > 0 ? 'text-success' : 'text-danger'}">
      <td>${r.fecha}</td>
      <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(r.concepto)}</td>
      <td class="text-end">${fmtEur(r.importe)}</td>
      <td class="text-end text-muted">${r.saldo != null ? fmtEur(r.saldo) : '—'}</td>
    </tr>`).join('');

  const remaining = data.total - data.rows.length;
  el('previewMore').textContent = remaining > 0 ? `+ ${remaining} filas más...` : '';

  // Warnings
  el('previewWarnings').innerHTML = data.warnings.map(w =>
    `<div class="alert alert-warning py-1 px-3 mb-1 small">
       <i class="bi bi-exclamation-circle me-1"></i>${escHtml(w)}
     </div>`).join('');

  // Update submit button label
  updateSubmitLabel();

  el('previewSection').classList.remove('d-none');
}

function renderPeriodCards() {
  const container = el('periodCards');
  // Header with select-all toggle (only if more than 1 period)
  let headerHtml = '';
  if (detectedPeriods.length > 1) {
    headerHtml = `
    <div class="period-select-header mb-2">
      <label class="period-select-all-label">
        <input type="checkbox" id="selectAllPeriods" checked onchange="toggleAllPeriods(this.checked)">
        <span>Seleccionar todos (${detectedPeriods.length} períodos)</span>
      </label>
    </div>`;
  }
  container.innerHTML = headerHtml + detectedPeriods.map((p, i) => `
    <div class="period-card ${p.selected ? '' : 'period-card-deselected'}" id="pcard-${i}">
      <div class="period-card-head">
        ${detectedPeriods.length > 1
          ? `<input type="checkbox" class="period-cb" ${p.selected ? 'checked' : ''}
               onchange="togglePeriod(${i}, this.checked)" style="accent-color:var(--blue);cursor:pointer">`
          : `<i class="bi bi-calendar3-range text-accent-blue"></i>`}
        <div class="period-card-dates">${p.date_from} → ${p.date_to}</div>
        <div class="period-card-count">${p._count} ops</div>
      </div>
      <input type="text" class="form-control-custom period-name-input mt-2"
             value="${escHtml(p.name)}"
             placeholder="Nombre del período"
             oninput="updatePeriodName(${i}, this.value)">
      <div class="period-card-metrics mt-2">
        <span class="pm-income"><i class="bi bi-arrow-down-circle me-1"></i>${fmtEur(p._ingresos)}</span>
        <span class="pm-expense"><i class="bi bi-arrow-up-circle me-1"></i>${fmtEur(p._gastos)}</span>
      </div>
      <div class="period-card-saldo mt-2">
        <label class="form-label-custom mb-1" style="font-size:10px">
          Saldo inicial <small class="text-muted">(opcional)</small>
        </label>
        <div class="input-group-custom">
          <span class="input-prefix">€</span>
          <input type="text" class="form-control-custom" style="font-size:12px;padding:5px 8px 5px 20px"
                 placeholder="0,00" value="${p.saldo_inicial != null ? p.saldo_inicial : ''}"
                 oninput="updatePeriodSaldo(${i}, this.value)">
        </div>
      </div>
    </div>`).join('');
}

function togglePeriod(i, checked) {
  detectedPeriods[i].selected = checked;
  const card = el(`pcard-${i}`);
  if (card) card.classList.toggle('period-card-deselected', !checked);
  // Update select-all checkbox state
  const allChecked = detectedPeriods.every(p => p.selected);
  const someChecked = detectedPeriods.some(p => p.selected);
  const masterCb = el('selectAllPeriods');
  if (masterCb) { masterCb.checked = allChecked; masterCb.indeterminate = !allChecked && someChecked; }
  updateSubmitLabel();
}

function toggleAllPeriods(checked) {
  detectedPeriods.forEach((p, i) => {
    p.selected = checked;
    const card = el(`pcard-${i}`);
    if (card) card.classList.toggle('period-card-deselected', !checked);
    const cb = document.querySelector(`#pcard-${i} .period-cb`);
    if (cb) cb.checked = checked;
  });
  updateSubmitLabel();
}

function updatePeriodName(i, val)  { detectedPeriods[i].name = val; updateSubmitLabel(); }
function updatePeriodSaldo(i, val) {
  const n = parseFloat(val.replace(',', '.'));
  detectedPeriods[i].saldo_inicial = isNaN(n) ? null : n;
}

function updateSubmitLabel() {
  const selected = detectedPeriods.filter(p => p.selected);
  const n = selected.length;
  el('submitText').innerHTML = n === 0
    ? `<i class="bi bi-upload me-2"></i>Importar`
    : `<i class="bi bi-upload me-2"></i>Importar ${n} período${n !== 1 ? 's' : ''}`;
  el('submitBtn').disabled = n === 0;
}

// ── Form submit ───────────────────────────────────────────────────────────────
document.getElementById('uploadForm').addEventListener('submit', e => {
  // Only include selected periods
  const config = detectedPeriods
    .filter(p => p.selected)
    .map(p => ({
      name:          p.name,
      date_from:     p.date_from,
      date_to:       p.date_to,
      saldo_inicial: p.saldo_inicial,
    }));
  if (!config.length) { e.preventDefault(); return; }
  el('periodsConfigInput').value = JSON.stringify(config);

  submitBtn.querySelector('.btn-text').classList.add('d-none');
  submitBtn.querySelector('.btn-loading').classList.remove('d-none');
  submitBtn.disabled = true;
});

// ── Drop zone states ──────────────────────────────────────────────────────────
function setDropState(state, filename) {
  const icon = el('dropIcon');
  const text = el('dropText');
  const sub  = el('dropSub');
  dropZone.classList.remove('has-file', 'has-error');

  if (state === 'loading') {
    icon.className = 'bi bi-hourglass-split text-muted';
    text.innerHTML = `<span class="text-muted">Procesando ${escHtml(filename)}…</span>`;
    sub.textContent = '';
  } else if (state === 'ok') {
    dropZone.classList.add('has-file');
    icon.className = 'bi bi-file-earmark-check-fill';
    text.innerHTML = `<span class="fw-600">${escHtml(filename)}</span>`;
    sub.textContent = 'Archivo listo · haz clic para cambiar';
  } else if (state === 'error') {
    icon.className = 'bi bi-file-earmark-x-fill';
    text.innerHTML = `<span class="text-danger">${escHtml(filename)}</span>`;
    sub.textContent = 'Error al procesar · haz clic para intentar con otro archivo';
  }
}

function showError(msg) {
  el('parseError').classList.remove('d-none');
  el('parseErrorMsg').textContent = msg;
}
function hideError() {
  el('parseError').classList.add('d-none');
}

function resetUpload() {
  fileInput.value = '';
  detectedPeriods = [];
  el('previewSection').classList.add('d-none');
  el('parsingSpinner').classList.add('d-none');
  hideError();
  el('dropIcon').className = 'bi bi-file-earmark-arrow-up';
  el('dropText').innerHTML = 'Arrastra tu CSV aquí o <span class="text-accent-green">haz clic para seleccionar</span>';
  el('dropSub').textContent = 'Compatible con CaixaBank, BBVA, Santander, Sabadell y cualquier CSV con fecha e importe';
  dropZone.classList.remove('has-file', 'has-error', 'dragover');
  submitBtn.disabled = false;
  submitBtn.querySelector('.btn-text').classList.remove('d-none');
  submitBtn.querySelector('.btn-loading').classList.add('d-none');
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function el(id)    { return document.getElementById(id); }
function fmtEur(v) { return new Intl.NumberFormat('es-ES', { style:'currency', currency:'EUR' }).format(v); }
function escHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
