// File: frontend/static/js/app/bao_cao_charts.js
// Advanced Analytics page — ECharts initialisation & live filter updates.

const PIE_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#06b6d4', '#f97316',
  '#84cc16', '#64748b',
];

let pieChart = null;
let barChart = null;

// ── Helpers ────────────────────────────────────────────────────────────────

function el(id) { return document.getElementById(id); }

function setInner(id, html) {
  const node = el(id);
  if (node) node.innerHTML = html;
}

function setText(id, val) {
  const node = el(id);
  if (node) node.textContent = val;
}

function buildParams() {
  const p = new URLSearchParams();
  const tu  = el('tu-ngay')?.value;
  const den = el('den-ngay')?.value;
  const pl  = el('phan-loai')?.value;
  const dt  = el('loai-dac-thu')?.value;
  if (tu)  p.set('tu_ngay',   tu);
  if (den) p.set('den_ngay',  den);
  if (pl)  p.set('phan_loai', pl);
  if (dt)  p.set('loai_hs_dac_thu', dt);
  return p;
}

function showLoading(on) {
  const btn = el('btn-refresh');
  if (!btn) return;
  btn.disabled = on;
  btn.textContent = on ? 'Đang tải…' : 'Làm mới';
}

function showError(msg) {
  setInner('bao-cao-error', `
    <div class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
      ⚠️ ${msg}
    </div>`);
}

function clearError() { setInner('bao-cao-error', ''); }

// ── Data updaters ──────────────────────────────────────────────────────────

function updateSummary(s) {
  setText('stat-total', Number(s.total).toLocaleString('vi'));
  setText('stat-draft', Number(s.draft).toLocaleString('vi'));
  setText('stat-sdt',   Number(s.co_sdt).toLocaleString('vi'));
  setText('stat-stk',   Number(s.co_stk).toLocaleString('vi'));
}

function updatePieChart(byPhanLoai) {
  if (!pieChart) return;
  const data = Object.entries(byPhanLoai).map(([name, value]) => ({ name, value }));
  if (!data.length) {
    pieChart.showLoading({ text: 'Không có dữ liệu', textColor: '#94a3b8', maskColor: 'transparent' });
    return;
  }
  pieChart.hideLoading();
  pieChart.setOption({ series: [{ data }] }, /* notMerge= */ false);
}

function updateBarChart(byMonth) {
  if (!barChart) return;
  if (!byMonth.length) {
    barChart.showLoading({ text: 'Không có dữ liệu', textColor: '#94a3b8', maskColor: 'transparent' });
    return;
  }
  barChart.hideLoading();
  barChart.setOption({
    xAxis: { data: byMonth.map(d => d.month) },
    series: [{ data: byMonth.map(d => d.count) }],
  }, false);
}

function updateTable(rows) {
  if (!rows.length) {
    setInner('bao-cao-table-body', `
      <tr><td colspan="3" style="text-align:center;padding:2rem;color:#94a3b8;font-size:.875rem">
        Không có dữ liệu để hiển thị
      </td></tr>`);
    return;
  }

  const html = rows.map((r, i) => `
    <tr>
      <td>
        <span style="display:inline-flex;align-items:center;gap:.5rem">
          <span style="width:.75rem;height:.75rem;border-radius:9999px;background:${PIE_COLORS[i % PIE_COLORS.length]};flex-shrink:0"></span>
          ${r.phan_loai}
        </span>
      </td>
      <td style="text-align:center;font-weight:600;color:#1e293b">${Number(r.count).toLocaleString('vi')}</td>
      <td>
        <div style="display:flex;align-items:center;gap:.5rem">
          <div style="flex:1;height:6px;border-radius:9999px;background:#f1f5f9;overflow:hidden">
            <div style="height:6px;border-radius:9999px;background:${PIE_COLORS[i % PIE_COLORS.length]};width:${r.pct}%;transition:width .4s ease"></div>
          </div>
          <span style="font-size:.75rem;color:#64748b;min-width:2.5rem;text-align:right">${r.pct}%</span>
        </div>
      </td>
    </tr>`).join('');
  setInner('bao-cao-table-body', html);
}

// ── Fetch & dispatch ───────────────────────────────────────────────────────

async function loadStats() {
  clearError();
  showLoading(true);
  try {
    const resp = await fetch(`/bao-cao/api/thong-ke?${buildParams()}`);
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(txt || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    updateSummary(data.summary);
    updatePieChart(data.by_phan_loai);
    updateBarChart(data.by_month);
    updateTable(data.table);
  } catch (err) {
    console.error('[bao_cao]', err);
    showError(err.message || 'Lỗi không xác định khi tải dữ liệu thống kê.');
  } finally {
    showLoading(false);
  }
}

// ── Chart initialisation ───────────────────────────────────────────────────

function initPieChart() {
  const node = el('chart-pie');
  if (!node || typeof echarts === 'undefined') return;

  pieChart = echarts.init(node);
  pieChart.setOption({
    backgroundColor: 'transparent',
    color: PIE_COLORS,
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/><strong>{c}</strong> hồ sơ ({d}%)',
      backgroundColor: 'rgba(255,255,255,.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b', fontSize: 12 },
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      left: 'center',
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#64748b', fontSize: 11 },
    },
    series: [{
      name: 'Phân loại',
      type: 'pie',
      radius: ['38%', '68%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      label: { show: false },
      emphasis: {
        label: { show: true, fontWeight: 'bold', color: '#1e293b', fontSize: 13 },
        scaleSize: 6,
      },
      data: [],
    }],
  });
  pieChart.showLoading({ text: 'Đang tải…', textColor: '#94a3b8', maskColor: 'rgba(255,255,255,.6)' });
}

function initBarChart() {
  const node = el('chart-bar');
  if (!node || typeof echarts === 'undefined') return;

  barChart = echarts.init(node);
  barChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255,255,255,.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b', fontSize: 12 },
      formatter: (params) => {
        const p = params[0];
        return `${p.axisValue}<br/><strong>${p.value}</strong> hồ sơ`;
      },
    },
    grid: { left: '3%', right: '4%', bottom: '18%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: [],
      axisLabel: { color: '#64748b', fontSize: 10, rotate: 35, interval: 0 },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [{
      name: 'Số hồ sơ nhập mới',
      type: 'bar',
      data: [],
      barMaxWidth: 40,
      itemStyle: {
        borderRadius: [5, 5, 0, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#6366f1' },
          ],
        },
      },
      label: {
        show: true,
        position: 'top',
        color: '#64748b',
        fontSize: 11,
        formatter: '{c}',
      },
    }],
  });
  barChart.showLoading({ text: 'Đang tải…', textColor: '#94a3b8', maskColor: 'rgba(255,255,255,.6)' });
}

// ── Boot ───────────────────────────────────────────────────────────────────

function resetFilters() {
  const ids = ['tu-ngay', 'den-ngay', 'phan-loai', 'loai-dac-thu'];
  ids.forEach(id => { const n = el(id); if (n) n.value = ''; });
  loadStats();
}

// ── Excel export ────────────────────────────────────────────────────────────

function exportXlsx() {
  const btn = el('btn-export');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `
      <svg class="w-3.5 h-3.5 inline mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      Đang xuất…`;
  }

  // Navigate to the export endpoint — browser triggers file download automatically
  window.location.href = `/bao-cao/export-xlsx?${buildParams()}`;

  // Re-enable button after 4s (download has started by then)
  setTimeout(() => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg class="w-3.5 h-3.5 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
        </svg>
        Xuất Excel (.xlsx)`;
    }
  }, 4000);
}

function initCharts() {
  initPieChart();
  initBarChart();
  loadStats();

  window.addEventListener('resize', () => {
    pieChart?.resize();
    barChart?.resize();
  });
}

document.addEventListener('DOMContentLoaded', initCharts);
