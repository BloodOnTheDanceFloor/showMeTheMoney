async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('Failed to fetch ' + path);
  return await res.json();
}

function getCssVar(name) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name);
  return (v || '').trim() || undefined;
}

function applyTheme(theme) {
  const t = theme || localStorage.getItem('theme') || 'classic';
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
}

function setupThemeSelector(onChange) {
  const sel = document.getElementById('themeSelect');
  if (!sel) return;
  const cur = localStorage.getItem('theme') || 'classic';
  sel.value = cur;
  sel.addEventListener('change', () => {
    applyTheme(sel.value);
    if (typeof onChange === 'function') onChange(sel.value);
  });
}

function fmtPnl(p) {
  const cls = p >= 0 ? 'pnl-pos' : 'pnl-neg';
  const v = (Math.round(p * 100) / 100).toLocaleString();
  return `<span class="${cls}">${v}</span>`;
}

function renderMonthlyChart(months) {
  const labels = months.map(m => m.month);
  const data = months.map(m => m.total_pnl);
  const ctx = document.getElementById('monthlyChart');
  if (window.__monthlyChart) { window.__monthlyChart.destroy(); }
  const up = getCssVar('--up') || 'rgba(220, 38, 38, 0.8)';
  const down = getCssVar('--down') || 'rgba(22, 163, 74, 0.8)';
  window.__monthlyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '当月累计盈亏',
        data,
        backgroundColor: data.map(v => v >= 0 ? up : down)
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } },
      plugins: { legend: { display: false } }
    }
  });
}

function renderMonthsList(months) {
  const box = document.getElementById('monthsList');
  box.innerHTML = months.map(m => {
    const ops = Array.isArray(m.stocks) ? m.stocks.length : 0;
    const tradesTotal = Array.isArray(m.stocks) ? m.stocks.reduce((acc, s) => acc + (s.trade_count || 0), 0) : 0;
    const chipsHtml = (m.stocks || []).map(s => {
      const cls = (s.pnl || 0) >= 0 ? 'chip up' : 'chip down';
      const name = s.name ? ` ${s.name}` : '';
      return `
        <a class="${cls}" href="stock.html?code=${encodeURIComponent(s.code)}">
          <span class="code">${s.code}${name}</span>
          <span class="pnl">${fmtPnl(s.pnl)}</span>
        </a>
      `;
    }).join('');
    return `
      <div class="month">
        <div class="head">
          <div class="m">${m.month}</div>
          <div class="p">
            <span class="badge">当月盈亏：${fmtPnl(m.total_pnl)}</span>
            <span class="meta">个股数：${ops}；撮合笔数：${tradesTotal}</span>
          </div>
        </div>
        <div class="chips">${chipsHtml}</div>
      </div>
    `;
  }).join('');
}

function renderStocksTable(stocks, sortKey = 'total_pnl', sortDir = 'desc') {
  const box = document.getElementById('stocksTable');
  const sorted = (stocks || []).slice().sort((a, b) => {
    const va = a?.[sortKey];
    const vb = b?.[sortKey];
    const na = (typeof va === 'number') ? va : (typeof va === 'string' ? va : -Infinity);
    const nb = (typeof vb === 'number') ? vb : (typeof vb === 'string' ? vb : -Infinity);
    if (typeof na === 'string' && typeof nb === 'string') {
      return (sortDir === 'asc' ? na.localeCompare(nb) : nb.localeCompare(na));
    }
    return (sortDir === 'asc' ? (na - nb) : (nb - na));
  });
  const rows = sorted.map(s => `
    <tr>
      <td><a href="stock.html?code=${encodeURIComponent(s.code)}">${s.code}</a></td>
      <td>${s.name || ''}</td>
      <td>${s.trade_count}</td>
      <td>${(s['win_rate_%'] ?? 0).toFixed(2)}%</td>
      <td>${fmtPnl(s.total_pnl)}</td>
      <td>${fmtPnl(s.max_win ?? 0)}</td>
      <td>${fmtPnl(s.max_loss ?? 0)}</td>
      <td>${(s.avg_hold_days ?? 0).toFixed(1)}</td>
      <td>${(s['avg_ret_%'] ?? 0).toFixed(2)}%</td>
    </tr>
  `).join('');
  const arrow = sortDir === 'asc' ? '↑' : '↓';
  box.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th class="sortable" data-key="code">代码 ${sortKey==='code'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="name">名称 ${sortKey==='name'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="trade_count">笔数 ${sortKey==='trade_count'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="win_rate_%">胜率% ${sortKey==='win_rate_%'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="total_pnl">总盈亏 ${sortKey==='total_pnl'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="max_win">最大盈利 ${sortKey==='max_win'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="max_loss">最大亏损 ${sortKey==='max_loss'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="avg_hold_days">平均持仓天数 ${sortKey==='avg_hold_days'?`<span class="sort">${arrow}</span>`:''}</th>
          <th class="sortable" data-key="avg_ret_%">平均收益率% ${sortKey==='avg_ret_%'?`<span class="sort">${arrow}</span>`:''}</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  // 绑定点击排序事件
  box.querySelectorAll('th.sortable').forEach(th => {
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const key = th.getAttribute('data-key');
      const nextDir = (key === sortKey && sortDir === 'desc') ? 'asc' : (key === sortKey && sortDir === 'asc' ? 'desc' : 'desc');
      renderStocksTable(stocks, key, nextDir);
    });
  });
}

async function init() {
  try {
    applyTheme();
    const months = await fetchJSON('data/monthly.json');
    renderMonthlyChart(months);
    renderMonthsList(months);
    setupThemeSelector(() => renderMonthlyChart(months));

    const stocks = await fetchJSON('data/stocks.json');
    renderStocksTable(stocks, 'total_pnl', 'desc');
  } catch (e) {
    console.error(e);
    alert('加载数据失败，请确认已生成 data/*.json');
  }
}

init();