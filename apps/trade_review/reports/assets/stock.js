function getParam(name) {
  const u = new URL(window.location.href);
  return u.searchParams.get(name);
}

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('Failed to fetch ' + path);
  return await res.json();
}

function getCssVar(name) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name);
  return (v || '').trim() || undefined;
}

// Register zoom/pan plugin if available
try {
  const zoomPlugin = (window['chartjs-plugin-zoom'] && window['chartjs-plugin-zoom'].default) || window['ChartZoom'];
  if (zoomPlugin) { Chart.register(zoomPlugin); }
} catch (e) { console.warn('zoom plugin not available', e); }

function applyTheme(theme) {
  const t = theme || 'dark';
  document.documentElement.setAttribute('data-theme', t);
  try { localStorage.setItem('theme', t); } catch (e) {}
}

function setupThemeSelector(onChange) {
  // 主题选择器已移除，默认使用暗色主题
  return;
}

function setupFontSizeControl() {
  const el = document.getElementById('fontSize');
  const txt = document.getElementById('fontSizeVal');
  if (!el) return;
  const saved = Number(localStorage.getItem('font-scale') || '1');
  const clamp = (v) => Math.min(1.5, Math.max(0.85, v));
  const setScale = (v) => {
    const s = clamp(Number(v) || 1);
    document.documentElement.style.setProperty('--font-scale', s);
    try { localStorage.setItem('font-scale', String(s)); } catch (e) {}
    if (txt) txt.textContent = `${(s*100).toFixed(0)}%`;
  };
  el.value = String(saved);
  setScale(saved);
  el.addEventListener('input', () => setScale(el.value));
}

function fmtPnl(p) {
  const cls = p >= 0 ? 'pnl-pos' : 'pnl-neg';
  const v = (Math.round(p * 100) / 100).toLocaleString();
  return `<span class="${cls}">${v}</span>`;
}

function renderSummary(s) {
  const box = document.getElementById('stockSummary');
  box.innerHTML = `
    <div class="summary">
      <div class="k"><div class="t">交易笔数</div><div class="v">${s.trade_count}</div></div>
      <div class="k"><div class="t">总盈亏</div><div class="v">${fmtPnl(s.total_pnl)}</div></div>
      <div class="k"><div class="t">胜率%</div><div class="v">${(s['win_rate_%'] ?? 0).toFixed(2)}%</div></div>
      <div class="k"><div class="t">最大盈利</div><div class="v">${fmtPnl(s.max_win ?? 0)}</div></div>
      <div class="k"><div class="t">最大亏损</div><div class="v">${fmtPnl(s.max_loss ?? 0)}</div></div>
      <div class="k"><div class="t">最大回撤%</div><div class="v">${(s['max_drawdown_%'] ?? 0).toFixed(2)}%</div></div>
      <div class="k"><div class="t">平均持仓天数</div><div class="v">${(s.avg_hold_days ?? 0).toFixed(1)}</div></div>
      <div class="k"><div class="t">平均收益率%</div><div class="v">${(s['avg_ret_%'] ?? 0).toFixed(2)}%</div></div>
    </div>
  `;
}

function renderEquityChart(trades) {
  const labels = trades.map(t => t.sell_date || t.sell_dt);
  let cum = 0;
  const data = trades.map(t => { cum += (t.pnl || 0); return cum; });
  const ctx = document.getElementById('stockEquityChart');
  if (window.__equityChart) { window.__equityChart.destroy(); }
  const accent = getCssVar('--accent') || '#4FC3F7';
  const grid = getCssVar('--border') || '#1f2937';
  const text = getCssVar('--text') || '#e5e7eb';
  const gctx = ctx.getContext('2d');
  const grad = gctx.createLinearGradient(0, 0, 0, ctx.height);
  grad.addColorStop(0, 'rgba(79, 195, 247, 0.35)');
  grad.addColorStop(1, 'rgba(79, 195, 247, 0.05)');
  window.__equityChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label: '累计盈亏（元）', data, borderColor: accent, backgroundColor: grad, fill: true }] },
    options: {
      responsive: true,
      plugins: { legend: { display: false }, zoom: { zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }, pan: { enabled: true, mode: 'x' } } },
      scales: {
        x: { ticks: { color: text }, grid: { color: grid } },
        y: { ticks: { color: text }, grid: { color: grid } }
      }
    }
  });
}

function renderTrades(trades) {
  const box = document.getElementById('stockTrades');
  const rows = trades.map(t => {
    const buyCost = Number(t.buy_cost_net ?? 0);
    const sellIn = Number(t.sell_proceeds_net ?? 0);
    const fees = Number(t.fees_total ?? 0);
    const pnl = sellIn - buyCost - fees; // 新公式：盈亏 = 卖出净收入 - 买入净支出 - 费用
    const retPct = buyCost > 0 ? (pnl / buyCost) * 100 : 0; // 新公式：收益率 = 盈亏 / 买入净支出
    return `
    <tr>
      <td>${t.sell_date}</td>
      <td>${t.qty}</td>
      <td>${(t.avg_buy_price ?? 0).toFixed(4)}</td>
      <td>${(t.avg_sell_price ?? 0).toFixed(4)}</td>
      <td>${buyCost.toFixed(2)} 元</td>
      <td>${sellIn.toFixed(2)} 元</td>
      <td>${fees.toFixed(2)} 元</td>
      <td>${fmtPnl(pnl)} 元</td>
      <td>${retPct.toFixed(2)}%</td>
      <td>${(t.hold_days ?? 0).toFixed(0)}</td>
    </tr>
  `}).join('');
  box.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>卖出日期</th><th>数量</th><th>均买价</th><th>均卖价</th>
          <th>买入净支出（元）</th><th>卖出净收入（元）</th><th>费用（元）</th>
          <th>盈亏（元）</th><th>收益率（%）</th><th>持仓天数</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  // 同步渲染交易盈亏柱状图（新公式）
  try {
    const ctx = document.getElementById('stockTradesChart');
    if (window.__tradesChart) { window.__tradesChart.destroy(); }
    const labels = trades.map(t => t.sell_date);
    const data = trades.map(t => (Number(t.sell_proceeds_net ?? 0) - Number(t.buy_cost_net ?? 0) - Number(t.fees_total ?? 0)));
    const up = getCssVar('--up') || 'rgba(255, 82, 82, 0.8)';
    const down = getCssVar('--down') || 'rgba(0, 230, 118, 0.8)';
    const grid = getCssVar('--border') || '#1f2937';
    const text = getCssVar('--text') || '#e5e7eb';
    const gctx = ctx.getContext('2d');
    const gradUp = gctx.createLinearGradient(0, 0, 0, ctx.height);
    gradUp.addColorStop(0, 'rgba(255, 82, 82, 0.85)');
    gradUp.addColorStop(1, 'rgba(255, 82, 82, 0.20)');
    const gradDown = gctx.createLinearGradient(0, 0, 0, ctx.height);
    gradDown.addColorStop(0, 'rgba(0, 230, 118, 0.85)');
    gradDown.addColorStop(1, 'rgba(0, 230, 118, 0.20)');
    window.__tradesChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: '单笔盈亏（元）', data, backgroundColor: data.map(v => v >= 0 ? gradUp : gradDown) }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `盈亏：${ctx.parsed.y.toFixed(2)} 元` } }, zoom: { zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }, pan: { enabled: true, mode: 'x' } } },
        scales: { x: { ticks: { color: text }, grid: { color: grid } }, y: { ticks: { color: text }, grid: { color: grid }, beginAtZero: true } }
      }
    });
  } catch (e) { console.warn('trades chart failed', e); }
}

function renderRaw(records) {
  const box = document.getElementById('rawRecords');
  const rows = records.map(r => {
    const cls = (r.side === '买入') ? 'row-buy' : (r.side === '卖出' ? 'row-sell' : '');
    return `
    <tr class="${cls}">
      <td>${r.date}</td><td>${r.time}</td><td>${r.side}</td>
      <td>${r.qty}</td><td>${(r.price ?? 0).toFixed(4)}</td>
      <td>${(r.fee_total ?? 0).toFixed(2)}</td><td>${(r.amount ?? 0).toFixed(2)}</td>
      <td>${(r.net_amount ?? 0).toFixed(2)}</td><td>${r.remark || ''}</td>
    </tr>
  `}).join('');
  box.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>日期</th><th>时间</th><th>方向</th><th>数量</th><th>价格</th>
          <th>费用</th><th>成交金额</th><th>清算金额</th><th>备注</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function computeMonthly(trades) {
  const map = new Map();
  trades.forEach(t => {
    const d = (t.sell_date || t.sell_dt || '').slice(0, 7);
    const buyCost = Number(t.buy_cost_net ?? 0);
    const sellIn = Number(t.sell_proceeds_net ?? 0);
    const fees = Number(t.fees_total ?? 0);
    const pnl = sellIn - buyCost - fees;
    const ret = buyCost > 0 ? pnl / buyCost : NaN;
    if (!map.has(d)) map.set(d, []);
    map.get(d).push({ pnl, ret });
  });
  const months = Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  return months.map(([m, arr]) => {
    const pnls = arr.map(x => x.pnl);
    const rets = arr.map(x => x.ret).filter(v => !isNaN(v));
    const wins = pnls.filter(v => v > 0);
    const losses = pnls.filter(v => v < 0).map(v => -v);
    const avgWin = wins.length ? wins.reduce((a, b) => a + b, 0) / wins.length : NaN;
    const avgLoss = losses.length ? losses.reduce((a, b) => a + b, 0) / losses.length : NaN;
    const plRatio = (!isNaN(avgWin) && !isNaN(avgLoss) && avgLoss > 0) ? (avgWin / avgLoss) : NaN;
    return {
      month: m,
      trade_count: arr.length,
      total_pnl: pnls.reduce((a, b) => a + b, 0),
      'win_rate_%': (wins.length / arr.length) * 100,
      'avg_ret_%': rets.length ? (rets.reduce((a, b) => a + b, 0) / rets.length) * 100 : NaN,
      avg_win: isNaN(avgWin) ? null : avgWin,
      avg_loss: isNaN(avgLoss) ? null : avgLoss,
      avg_win_loss_ratio: isNaN(plRatio) ? null : plRatio
    };
  });
}

function renderMonthlyDashboard(trades) {
  const months = computeMonthly(trades);
  const sel = document.getElementById('monthSelect');
  sel.innerHTML = months.map(m => `<option value="${m.month}">${m.month}</option>`).join('');
  const grid = getCssVar('--border') || '#1f2937';
  const text = getCssVar('--text') || '#e5e7eb';
  const up = getCssVar('--up') || 'rgba(239, 68, 68, 0.8)';
  const down = getCssVar('--down') || 'rgba(34, 197, 94, 0.8)';

  function update(month) {
    const m = months.find(x => x.month === month) || months[months.length - 1];
    const box = document.getElementById('monthSummary');
    box.innerHTML = `
      <div class="summary">
        <div class="k"><div class="t">月份</div><div class="v">${m.month}</div></div>
        <div class="k"><div class="t">撮合笔数</div><div class="v">${m.trade_count}</div></div>
        <div class="k"><div class="t">总盈亏</div><div class="v">${fmtPnl(m.total_pnl)}</div></div>
        <div class="k"><div class="t">胜率%</div><div class="v">${(m['win_rate_%'] ?? 0).toFixed(2)}%</div></div>
        <div class="k"><div class="t">平均收益率%</div><div class="v">${(m['avg_ret_%'] ?? 0).toFixed(2)}%</div></div>
        <div class="k"><div class="t">平均盈利</div><div class="v">${m.avg_win ? m.avg_win.toFixed(2) : '--'}</div></div>
        <div class="k"><div class="t">平均亏损</div><div class="v">${m.avg_loss ? m.avg_loss.toFixed(2) : '--'}</div></div>
        <div class="k"><div class="t">盈亏比</div><div class="v">${m.avg_win_loss_ratio ? m.avg_win_loss_ratio.toFixed(2) : '--'}</div></div>
      </div>
    `;
    const ctx = document.getElementById('monthEquityChart');
    if (window.__monthChart) { window.__monthChart.destroy(); }
    // 构造该月内的逐笔盈亏柱状图
    const monthTrades = trades.filter(t => (t.sell_date || t.sell_dt || '').slice(0, 7) === m.month);
    const labels = monthTrades.map(t => t.sell_date || t.sell_dt);
    const data = monthTrades.map(t => (Number(t.sell_proceeds_net ?? 0) - Number(t.buy_cost_net ?? 0) - Number(t.fees_total ?? 0)));
    window.__monthChart = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ label: `当月单笔盈亏（元）`, data, backgroundColor: data.map(v => v >= 0 ? up : down) }] },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `盈亏：${ctx.parsed.y.toFixed(2)} 元` } } },
        scales: { x: { ticks: { color: text }, grid: { color: grid } }, y: { ticks: { color: text }, grid: { color: grid }, beginAtZero: true } }
      }
    });
  }

  sel.addEventListener('change', () => update(sel.value));
  update(sel.value || (months[months.length - 1]?.month));
}

async function init() {
  const code = getParam('code');
  if (!code) { alert('缺少code参数'); return; }
  document.getElementById('stockTitle').textContent = `个股详情：${code}`;
  try {
    applyTheme();
    setupFontSizeControl();
    const data = await fetchJSON(`data/stock/${encodeURIComponent(code)}.json`);
    document.getElementById('stockTitle').textContent = `个股详情：${data.code} ${data.name || ''}`;
    renderSummary(data.summary || {});
    renderEquityChart(data.trades || []);
    renderTrades(data.trades || []);
    renderRaw(data.raw_records || []);
    renderMonthlyDashboard(data.trades || []);
  } catch (e) {
    console.error(e);
    alert('加载个股详情失败，请确认已生成对应JSON');
  }
}

init();