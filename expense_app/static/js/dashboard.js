// ── STATE ──
const state = {
  currentView: 'dashboard',
  txnType: 'expense',
  txnPage: 1,
  txnPerPage: 20,
  txnTotal: 0,
  categories: [],
  currentReport: 'monthly',
  trendChart: null,
  categoryChart: null,
  reportPieChart: null,
  reportBarChart: null,
};

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  initDateTime();
  loadDashboard();
  loadCategories();
  loadAlerts();
});

function initDateTime() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  const el = document.getElementById('txn-date');
  if (el) el.value = local.toISOString().slice(0, 16);
}

// ── NAVIGATION ──
function switchView(viewName, linkEl) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`view-${viewName}`).classList.add('active');
  if (linkEl) linkEl.classList.add('active');
  document.getElementById('page-title').textContent = viewName.charAt(0).toUpperCase() + viewName.slice(1);
  state.currentView = viewName;
  if (window.innerWidth <= 768) document.getElementById('sidebar').classList.remove('open');

  switch (viewName) {
    case 'dashboard': loadDashboard(); break;
    case 'transactions': loadTransactions(); populateCategoryFilter(); break;
    case 'reports': loadReport('monthly', document.querySelector('.rtab:nth-child(3)')); break;
    case 'budgets': loadBudgets(); break;
    case 'categories': loadCategories(); break;
    case 'insights': loadInsights(); break;
  }
  return false;
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ── API HELPERS ──
async function api(url, options = {}) {
  try {
    const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
    if (res.status === 401) { location.href = '/auth/login'; return null; }
    return res.ok ? await res.json() : null;
  } catch (e) { console.error(url, e); return null; }
}

// ── TOAST ──
function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = `toast ${type} show`;
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ── MODALS ──
function openModal(id) {
  const m = document.getElementById(id);
  if (!m) return;
  m.classList.add('active');
  if (id === 'add-transaction-modal') {
    document.getElementById('edit-txn-id').value = '';
    document.getElementById('txn-modal-title').textContent = 'Add Transaction';
    initDateTime();
    populateTxnCategories();
  }
  if (id === 'add-budget-modal') populateBudgetCategories();
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', e => { if (e.target === m) m.classList.remove('active'); });
});

// ── DASHBOARD ──
async function loadDashboard() {
  const [balance, monthReport, trend, catReport] = await Promise.all([
    api('/api/transactions/balance'),
    api('/api/reports/monthly'),
    api('/api/reports/chart/monthly-trend'),
    api('/api/reports/monthly'),
  ]);

  if (balance) {
    document.getElementById('stat-income').textContent = fmt(balance.income);
    document.getElementById('stat-expense').textContent = fmt(balance.expense);
    document.getElementById('stat-balance').textContent = fmt(balance.balance);
  }
  if (monthReport) {
    document.getElementById('stat-month-expense').textContent = fmt(monthReport.expense);
  }

  if (trend) renderTrendChart(trend);
  if (catReport) renderCategoryChart(catReport.category_breakdown);

  const txns = await api('/api/transactions/?per_page=8');
  if (txns) renderTxnList('recent-txns', txns.transactions, true);
}

// ── CHARTS ──
const chartDefaults = {
  color: 'rgba(255,255,255,0.7)',
  grid: 'rgba(255,255,255,0.05)',
};

function renderTrendChart(data) {
  const ctx = document.getElementById('trend-chart').getContext('2d');
  if (state.trendChart) state.trendChart.destroy();
  state.trendChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.month),
      datasets: [
        { label: 'Income', data: data.map(d => d.income), backgroundColor: 'rgba(74,222,128,0.7)', borderRadius: 6, borderSkipped: false },
        { label: 'Expense', data: data.map(d => d.expense), backgroundColor: 'rgba(248,113,113,0.7)', borderRadius: 6, borderSkipped: false },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: chartDefaults.color, padding: 16, usePointStyle: true } } },
      scales: {
        x: { ticks: { color: chartDefaults.color, font: { size: 11 } }, grid: { color: chartDefaults.grid } },
        y: { ticks: { color: chartDefaults.color, callback: v => '₹' + numShort(v) }, grid: { color: chartDefaults.grid } }
      }
    }
  });
}

function renderCategoryChart(breakdown) {
  const expenses = breakdown.filter(b => b.type === 'expense').slice(0, 7);
  if (!expenses.length) return;
  const ctx = document.getElementById('category-chart').getContext('2d');
  if (state.categoryChart) state.categoryChart.destroy();
  state.categoryChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: expenses.map(e => e.category),
      datasets: [{ data: expenses.map(e => e.amount), backgroundColor: expenses.map(e => e.color || '#6366f1'), borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: {
        legend: { position: 'right', labels: { color: chartDefaults.color, padding: 12, usePointStyle: true, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.raw.toLocaleString('en-IN')}` } }
      }
    }
  });
}

// ── TRANSACTIONS ──
async function loadTransactions() {
  const type = document.getElementById('filter-type')?.value || '';
  const catId = document.getElementById('filter-category')?.value || '';
  const start = document.getElementById('filter-start')?.value || '';
  const end = document.getElementById('filter-end')?.value || '';
  let url = `/api/transactions/?page=${state.txnPage}&per_page=${state.txnPerPage}`;
  if (type) url += `&type=${type}`;
  if (catId) url += `&category_id=${catId}`;
  if (start) url += `&start_date=${start}`;
  if (end) url += `&end_date=${end}`;
  const data = await api(url);
  if (!data) return;
  state.txnTotal = data.total;
  renderTxnTable(data.transactions);
  renderPagination(data.total, data.page, data.per_page);
}

function renderTxnList(containerId, txns, compact = false) {
  const container = document.getElementById(containerId);
  if (!txns.length) { container.innerHTML = '<div class="empty-state"><div class="empty-icon">💳</div><p>No transactions yet. Add your first one!</p></div>'; return; }
  container.innerHTML = txns.map(t => `
    <div class="txn-item">
      <div class="txn-cat-icon" style="background:${t.category_color}22">${t.category_icon}</div>
      <div class="txn-info">
        <div class="txn-cat-name">${t.category_name || 'Unknown'}</div>
        <div class="txn-sub-name">${t.subcategory_name || t.notes || '—'}</div>
      </div>
      <div class="txn-date">${fmtDate(t.date)}</div>
      <div class="txn-amount ${t.type}">${t.type === 'income' ? '+' : '-'}${fmt(t.amount)}</div>
      ${!compact ? `<div class="txn-actions">
        <button class="icon-btn" onclick="editTransaction(${t.id})" title="Edit">✎</button>
        <button class="icon-btn del" onclick="deleteTransaction(${t.id})" title="Delete">✕</button>
      </div>` : ''}
    </div>
  `).join('');
}

function renderTxnTable(txns) {
  const tbody = document.getElementById('txn-table-body');
  if (!txns.length) { tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--muted)">No transactions found</td></tr>'; return; }
  tbody.innerHTML = txns.map(t => `
    <tr>
      <td>${fmtDate(t.date)}</td>
      <td><span style="margin-right:6px">${t.category_icon}</span>${t.category_name || '—'}</td>
      <td>${t.subcategory_name || '—'}</td>
      <td>${t.notes || '—'}</td>
      <td><span class="badge ${t.type}">${t.type}</span></td>
      <td class="txn-amount ${t.type}" style="font-weight:700">${t.type === 'income' ? '+' : '-'}${fmt(t.amount)}</td>
      <td>
        <div class="txn-actions">
          <button class="icon-btn" onclick="editTransaction(${t.id})" title="Edit">✎</button>
          <button class="icon-btn del" onclick="deleteTransaction(${t.id})" title="Delete">✕</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function renderPagination(total, page, perPage) {
  const pages = Math.ceil(total / perPage);
  const container = document.getElementById('pagination');
  if (pages <= 1) { container.innerHTML = ''; return; }
  let html = '';
  if (page > 1) html += `<button class="page-btn" onclick="goPage(${page-1})">← Prev</button>`;
  for (let i = Math.max(1, page-2); i <= Math.min(pages, page+2); i++) {
    html += `<button class="page-btn ${i===page?'active':''}" onclick="goPage(${i})">${i}</button>`;
  }
  if (page < pages) html += `<button class="page-btn" onclick="goPage(${page+1})">Next →</button>`;
  container.innerHTML = html;
}

function goPage(p) { state.txnPage = p; loadTransactions(); }

async function editTransaction(id) {
  const data = await api(`/api/transactions/?per_page=1000`);
  const txn = data?.transactions?.find(t => t.id === id);
  if (!txn) return;
  openModal('add-transaction-modal');
  setTimeout(() => {
    document.getElementById('edit-txn-id').value = id;
    document.getElementById('txn-modal-title').textContent = 'Edit Transaction';
    setTxnType(txn.type);
    document.getElementById('txn-amount').value = txn.amount;
    const localDate = new Date(txn.date);
    const offset = localDate.getTimezoneOffset() * 60000;
    document.getElementById('txn-date').value = new Date(localDate.getTime() - offset).toISOString().slice(0, 16);
    document.getElementById('txn-notes').value = txn.notes || '';
    populateTxnCategories(txn.category_id, txn.subcategory_id);
  }, 50);
}

async function deleteTransaction(id) {
  if (!confirm('Delete this transaction?')) return;
  const res = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
  if (res.ok) {
    showToast('Transaction deleted', 'success');
    if (state.currentView === 'dashboard') loadDashboard();
    else loadTransactions();
    loadAlerts();
  } else showToast('Failed to delete', 'error');
}

async function saveTransaction() {
  const id = document.getElementById('edit-txn-id').value;
  const amount = parseFloat(document.getElementById('txn-amount').value);
  const catId = parseInt(document.getElementById('txn-category').value);
  const subId = document.getElementById('txn-subcategory').value;
  const date = document.getElementById('txn-date').value;
  const notes = document.getElementById('txn-notes').value;
  if (!amount || !catId) return showToast('Amount and category are required', 'error');
  const body = { amount, type: state.txnType, category_id: catId, notes, date: date ? new Date(date).toISOString() : undefined };
  if (subId) body.subcategory_id = parseInt(subId);
  const url = id ? `/api/transactions/${id}` : '/api/transactions/';
  const method = id ? 'PUT' : 'POST';
  const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (res.ok) {
    showToast(id ? 'Transaction updated!' : 'Transaction added!', 'success');
    closeModal('add-transaction-modal');
    if (state.currentView === 'dashboard') loadDashboard();
    else loadTransactions();
    loadAlerts();
  } else { const d = await res.json(); showToast(d.error || 'Save failed', 'error'); }
}

function setTxnType(type) {
  state.txnType = type;
  document.getElementById('type-expense').classList.toggle('active', type === 'expense');
  document.getElementById('type-income').classList.toggle('active', type === 'income');
  populateTxnCategories();
}

async function populateTxnCategories(selectedCatId = null, selectedSubId = null) {
  const cats = await api(`/api/categories/?type=${state.txnType}`);
  const catSel = document.getElementById('txn-category');
  catSel.innerHTML = '<option value="">Select category...</option>';
  (cats || []).forEach(c => catSel.innerHTML += `<option value="${c.id}" ${c.id === selectedCatId ? 'selected' : ''}>${c.icon} ${c.name}</option>`);
  if (selectedCatId) { catSel.value = selectedCatId; loadSubcategories(selectedSubId); }
  else loadSubcategories();
}

async function loadSubcategories(selectedSubId = null) {
  const catId = document.getElementById('txn-category').value;
  const subSel = document.getElementById('txn-subcategory');
  subSel.innerHTML = '<option value="">None</option>';
  if (!catId) return;
  const cats = await api('/api/categories/');
  const cat = (cats || []).find(c => c.id == catId);
  if (cat?.subcategories) {
    cat.subcategories.forEach(s => subSel.innerHTML += `<option value="${s.id}" ${s.id === selectedSubId ? 'selected' : ''}>${s.name}</option>`);
    if (selectedSubId) subSel.value = selectedSubId;
  }
}

async function populateCategoryFilter() {
  const cats = await api('/api/categories/');
  const sel = document.getElementById('filter-category');
  sel.innerHTML = '<option value="">All Categories</option>';
  (cats || []).forEach(c => sel.innerHTML += `<option value="${c.id}">${c.icon} ${c.name}</option>`);
}

function exportCSV() { window.location.href = '/api/transactions/export/csv'; }

// ── REPORTS ──
async function loadReport(period, btnEl) {
  state.currentReport = period;
  document.querySelectorAll('.rtab').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  let url = `/api/reports/${period}`;
  const controls = document.getElementById('report-period-controls');
  controls.innerHTML = '';

  if (period === 'monthly') {
    const now = new Date();
    controls.innerHTML = `
      <select id="rep-month" onchange="loadReport('monthly', document.querySelector('.rtab.active'))">
        ${[...Array(12)].map((_, i) => `<option value="${i+1}" ${i+1===now.getMonth()+1?'selected':''}>${new Date(2000,i).toLocaleString('default',{month:'long'})}</option>`).join('')}
      </select>
      <select id="rep-year" onchange="loadReport('monthly', document.querySelector('.rtab.active'))">
        ${[0,1,2].map(i => `<option value="${now.getFullYear()-i}" ${i===0?'selected':''}>${now.getFullYear()-i}</option>`).join('')}
      </select>`;
    const m = document.getElementById('rep-month')?.value;
    const y = document.getElementById('rep-year')?.value;
    if (m && y) url += `?month=${m}&year=${y}`;
  } else if (period === 'yearly') {
    const now = new Date();
    controls.innerHTML = `<select id="rep-year2" onchange="loadReport('yearly', document.querySelector('.rtab.active'))">
      ${[0,1,2].map(i => `<option value="${now.getFullYear()-i}" ${i===0?'selected':''}>${now.getFullYear()-i}</option>`).join('')}
    </select>`;
    const y = document.getElementById('rep-year2')?.value;
    if (y) url += `?year=${y}`;
  }

  const data = await api(url);
  if (!data) return;

  document.getElementById('report-stats').innerHTML = `
    <div class="report-stat"><div class="report-stat-label">Total Income</div><div class="report-stat-value" style="color:var(--income)">${fmt(data.income)}</div></div>
    <div class="report-stat"><div class="report-stat-label">Total Expenses</div><div class="report-stat-value" style="color:var(--expense)">${fmt(data.expense)}</div></div>
    <div class="report-stat"><div class="report-stat-label">Net Balance</div><div class="report-stat-value" style="color:${data.balance>=0?'var(--income)':'var(--expense)'}">${fmt(data.balance)}</div></div>
  `;

  const expenses = data.category_breakdown.filter(b => b.type === 'expense');
  const income = data.category_breakdown.filter(b => b.type === 'income');

  renderReportPie(expenses);
  renderReportBar([...expenses, ...income]);
  renderBreakdown(data.category_breakdown);
}

function renderReportPie(expenses) {
  const ctx = document.getElementById('report-pie-chart').getContext('2d');
  if (state.reportPieChart) state.reportPieChart.destroy();
  if (!expenses.length) return;
  state.reportPieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: expenses.map(e => e.category),
      datasets: [{ data: expenses.map(e => e.amount), backgroundColor: expenses.map(e => e.color || '#6366f1'), borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '60%',
      plugins: {
        legend: { position: 'bottom', labels: { color: chartDefaults.color, padding: 10, usePointStyle: true, font: { size: 10 } } },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.raw.toLocaleString('en-IN')}` } }
      }
    }
  });
}

function renderReportBar(breakdown) {
  const ctx = document.getElementById('report-bar-chart').getContext('2d');
  if (state.reportBarChart) state.reportBarChart.destroy();
  if (!breakdown.length) return;
  const sorted = breakdown.sort((a,b) => b.amount - a.amount).slice(0, 10);
  state.reportBarChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(d => d.category),
      datasets: [{ label: 'Amount', data: sorted.map(d => d.amount), backgroundColor: sorted.map(d => d.color || '#6366f1'), borderRadius: 6, borderSkipped: false }]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ₹${ctx.raw.toLocaleString('en-IN')}` } } },
      scales: {
        x: { ticks: { color: chartDefaults.color, callback: v => '₹' + numShort(v) }, grid: { color: chartDefaults.grid } },
        y: { ticks: { color: chartDefaults.color, font: { size: 11 } }, grid: { display: false } }
      }
    }
  });
}

function renderBreakdown(breakdown) {
  const container = document.getElementById('report-breakdown');
  if (!breakdown.length) { container.innerHTML = '<div class="empty-state"><div class="empty-icon">📊</div><p>No data for this period</p></div>'; return; }
  container.innerHTML = breakdown.map(b => `
    <div class="breakdown-item">
      <div class="breakdown-icon">${b.icon}</div>
      <div class="breakdown-info">
        <div class="breakdown-name">${b.category} <span class="badge ${b.type}" style="font-size:0.7rem">${b.type}</span></div>
        <div class="breakdown-amount" style="color:${b.type==='income'?'var(--income)':'var(--expense)'}">${fmt(b.amount)}</div>
      </div>
    </div>
  `).join('');
}

// ── BUDGETS ──
async function loadBudgets() {
  const now = new Date();
  document.getElementById('budget-month-label').textContent = now.toLocaleString('default', { month: 'long', year: 'numeric' });
  const budgets = await api(`/api/budgets/?month=${now.getMonth()+1}&year=${now.getFullYear()}`);
  const grid = document.getElementById('budgets-grid');
  if (!budgets?.length) { grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🎯</div><p>No budgets set. Click "+ Set Budget" to get started!</p></div>'; return; }
  grid.innerHTML = budgets.map(b => {
    const cls = b.percentage >= 100 ? 'danger' : b.percentage >= 80 ? 'warn' : 'safe';
    return `
      <div class="budget-card">
        <div class="budget-header">
          <div class="budget-icon">${b.category_icon}</div>
          <div><div class="budget-cat">${b.category_name}</div></div>
        </div>
        <div class="budget-amounts">
          <span>Spent: <span class="budget-spent">₹${b.spent.toLocaleString('en-IN')}</span></span>
          <span>Budget: ₹${b.amount.toLocaleString('en-IN')}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill ${cls}" style="width:${b.percentage}%"></div></div>
        <div class="budget-footer">
          <span>${b.percentage}% used • ₹${Math.max(0,b.remaining).toLocaleString('en-IN')} left</span>
          <button class="budget-delete" onclick="deleteBudget(${b.id})">✕ Remove</button>
        </div>
      </div>`;
  }).join('');
}

async function populateBudgetCategories() {
  const cats = await api('/api/categories/?type=expense');
  const sel = document.getElementById('budget-category');
  sel.innerHTML = (cats || []).map(c => `<option value="${c.id}">${c.icon} ${c.name}</option>`).join('');
}

async function saveBudget() {
  const catId = document.getElementById('budget-category').value;
  const amount = parseFloat(document.getElementById('budget-amount').value);
  if (!catId || !amount) return showToast('Fill all fields', 'error');
  const now = new Date();
  const res = await fetch('/api/budgets/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category_id: parseInt(catId), amount, month: now.getMonth()+1, year: now.getFullYear() })
  });
  if (res.ok) { showToast('Budget set!', 'success'); closeModal('add-budget-modal'); loadBudgets(); loadAlerts(); }
  else showToast('Failed', 'error');
}

async function deleteBudget(id) {
  if (!confirm('Remove this budget?')) return;
  const res = await fetch(`/api/budgets/${id}`, { method: 'DELETE' });
  if (res.ok) { showToast('Budget removed', 'success'); loadBudgets(); }
}

// ── CATEGORIES ──
async function loadCategories() {
  const type = document.getElementById('cat-type-filter')?.value || '';
  const url = type ? `/api/categories/?type=${type}` : '/api/categories/';
  const cats = await api(url);
  state.categories = cats || [];
  const grid = document.getElementById('categories-grid');
  if (!cats?.length) { grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🏷️</div><p>No categories found.</p></div>'; return; }
  grid.innerHTML = cats.map(c => `
    <div class="cat-card">
      <div class="cat-card-header">
        <div class="cat-card-icon" style="background:${c.color}22">${c.icon}</div>
        <div class="cat-card-info">
          <div class="cat-card-name">${c.name}</div>
          <div class="cat-card-type"><span class="badge ${c.type}">${c.type}</span></div>
        </div>
        <div class="cat-actions">
          <button class="icon-btn del" onclick="deleteCategory(${c.id})" title="Delete">✕</button>
        </div>
      </div>
      <div class="subs-list">
        ${c.subcategories.map(s => `<span class="sub-tag">${s.name}<button onclick="deleteSubcategory(${s.id})" title="Remove">✕</button></span>`).join('')}
      </div>
      <button class="add-sub-btn" onclick="openAddSubModal(${c.id})">+ Add Subcategory</button>
    </div>
  `).join('');
}

async function saveCategory() {
  const name = document.getElementById('cat-name').value.trim();
  const type = document.getElementById('cat-type').value;
  const icon = document.getElementById('cat-icon').value || '💰';
  const color = document.getElementById('cat-color').value;
  if (!name) return showToast('Name required', 'error');
  const res = await fetch('/api/categories/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, type, icon, color })
  });
  if (res.ok) { showToast('Category added!', 'success'); closeModal('add-category-modal'); loadCategories(); document.getElementById('cat-name').value = ''; }
  else showToast('Failed', 'error');
}

async function deleteCategory(id) {
  if (!confirm('Delete this category and all its transactions?')) return;
  const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
  if (res.ok) { showToast('Category deleted', 'success'); loadCategories(); }
  else showToast('Failed', 'error');
}

function openAddSubModal(catId) {
  document.getElementById('sub-cat-id').value = catId;
  document.getElementById('sub-name').value = '';
  openModal('add-subcategory-modal');
}

async function saveSubcategory() {
  const catId = document.getElementById('sub-cat-id').value;
  const name = document.getElementById('sub-name').value.trim();
  if (!name) return showToast('Name required', 'error');
  const res = await fetch(`/api/categories/${catId}/subcategories`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  });
  if (res.ok) { showToast('Subcategory added!', 'success'); closeModal('add-subcategory-modal'); loadCategories(); }
  else showToast('Failed', 'error');
}

async function deleteSubcategory(id) {
  const res = await fetch(`/api/categories/subcategories/${id}`, { method: 'DELETE' });
  if (res.ok) { showToast('Subcategory removed', 'success'); loadCategories(); }
}

// ── ALERTS ──
async function loadAlerts() {
  const alerts = await api('/api/budgets/alerts');
  const container = document.getElementById('alerts-container');
  if (!alerts?.length) { container.innerHTML = ''; return; }
  container.innerHTML = alerts.slice(0, 3).map(a => `
    <div class="alert-banner ${a.type}">${a.message}</div>
  `).join('');
}

// ── AI INSIGHTS ──
async function loadInsights() {
  document.getElementById('insights-grid').innerHTML = '<div style="color:var(--muted);padding:24px">Analyzing your spending patterns...</div>';
  document.getElementById('prediction-card').innerHTML = '<div style="color:var(--muted);padding:24px">Running prediction model...</div>';
  const [insights, prediction] = await Promise.all([api('/api/insights/'), api('/api/insights/predict')]);
  renderInsights(insights);
  renderPrediction(prediction);
}

function renderInsights(insights) {
  const grid = document.getElementById('insights-grid');
  if (!insights?.length) { grid.innerHTML = '<div class="empty-state"><div class="empty-icon">🤖</div><p>Add more transactions to get insights!</p></div>'; return; }
  grid.innerHTML = insights.map(i => `
    <div class="insight-card ${i.type}">
      <div class="insight-icon">${i.icon}</div>
      <div class="insight-title">${i.title}</div>
      <div class="insight-message">${i.message}</div>
    </div>
  `).join('');
}

function renderPrediction(pred) {
  const card = document.getElementById('prediction-card');
  if (!pred?.prediction) {
    card.innerHTML = `<div class="empty-state"><div class="empty-icon">🔮</div><p>${pred?.message || 'Not enough data for prediction'}</p></div>`;
    return;
  }
  const trendIcon = pred.trend === 'increasing' ? '📈' : pred.trend === 'decreasing' ? '📉' : '➡️';
  card.innerHTML = `
    <div class="prediction-main">
      <div>
        <div style="color:var(--muted);font-size:0.85rem;margin-bottom:6px">Predicted expenses for</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:12px">${pred.month}</div>
        <div class="prediction-value">${fmt(pred.prediction)}</div>
      </div>
      <div class="prediction-info">
        <div class="prediction-label">Trend: ${trendIcon} ${pred.trend}</div>
        <div class="prediction-meta" style="margin-top:8px">
          Confidence: <span class="confidence-badge ${pred.confidence}">${pred.confidence}</span>
        </div>
        <div style="color:var(--muted);font-size:0.82rem;margin-top:10px">
          Based on historical patterns using Linear Regression (R²: ${pred.r_squared})
        </div>
      </div>
    </div>
  `;
}

// ── LOGOUT ──
async function doLogout() {
  await fetch('/auth/logout', { method: 'POST' });
  location.href = '/auth/login';
}

// ── FORMATTERS ──
function fmt(amount) {
  return '₹' + Math.abs(amount).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
function numShort(n) {
  if (n >= 100000) return (n/100000).toFixed(1) + 'L';
  if (n >= 1000) return (n/1000).toFixed(0) + 'K';
  return n;
}
function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}
