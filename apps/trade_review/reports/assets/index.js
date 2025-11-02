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
  const t = theme || localStorage.getItem('theme') || 'classic';
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('theme', t);
}

function setupThemeSelector(onChange) {
  // 新的主题切换按钮
  const lightBtn = document.getElementById('themeLight');
  const darkBtn = document.getElementById('themeDark');
  
  if (lightBtn && darkBtn) {
    const cur = localStorage.getItem('theme') || 'light';
    
    // 设置初始状态
    if (cur === 'light') {
      lightBtn.classList.add('active');
    } else {
      darkBtn.classList.add('active');
    }
    
    // 绑定点击事件
    lightBtn.addEventListener('click', () => {
      applyTheme('light');
      lightBtn.classList.add('active');
      darkBtn.classList.remove('active');
      if (typeof onChange === 'function') onChange('light');
    });
    
    darkBtn.addEventListener('click', () => {
      applyTheme('dark');
      darkBtn.classList.add('active');
      lightBtn.classList.remove('active');
      if (typeof onChange === 'function') onChange('dark');
    });
  }
  
  // 保留旧的下拉选择器支持
  const sel = document.getElementById('themeSelect');
  if (sel) {
    const cur = localStorage.getItem('theme') || 'classic';
    sel.value = cur;
    sel.addEventListener('change', () => {
      applyTheme(sel.value);
      if (typeof onChange === 'function') onChange(sel.value);
    });
  }
}

function setupFontSizeControl() {
  // 新的字体大小按钮
  const increaseBtn = document.getElementById('fontSizeIncrease');
  const decreaseBtn = document.getElementById('fontSizeDecrease');
  
  if (increaseBtn && decreaseBtn) {
    const saved = Number(localStorage.getItem('font-scale') || '1');
    const clamp = (v) => Math.min(1.5, Math.max(0.85, v));
    const setScale = (v) => {
      const s = clamp(Number(v) || 1);
      document.documentElement.style.setProperty('--font-scale', s);
      try { localStorage.setItem('font-scale', String(s)); } catch (e) {}
    };
    
    // 设置初始字体大小
    setScale(saved);
    
    // 绑定点击事件
    increaseBtn.addEventListener('click', () => {
      const currentScale = Number(localStorage.getItem('font-scale') || '1');
      setScale(currentScale + 0.1);
    });
    
    decreaseBtn.addEventListener('click', () => {
      const currentScale = Number(localStorage.getItem('font-scale') || '1');
      setScale(currentScale - 0.1);
    });
  }
  
  // 保留旧的滑块控制支持
  const el = document.getElementById('fontSize');
  const txt = document.getElementById('fontSizeVal');
  if (el) {
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
  const up = getCssVar('--up') || 'rgba(255, 82, 82, 0.8)';
  const down = getCssVar('--down') || 'rgba(0, 230, 118, 0.8)';
  const gctx = ctx.getContext('2d');
  const gradUp = gctx.createLinearGradient(0, 0, 0, ctx.height);
  gradUp.addColorStop(0, 'rgba(255, 82, 82, 0.85)');
  gradUp.addColorStop(1, 'rgba(255, 82, 82, 0.20)');
  const gradDown = gctx.createLinearGradient(0, 0, 0, ctx.height);
  gradDown.addColorStop(0, 'rgba(0, 230, 118, 0.85)');
  gradDown.addColorStop(1, 'rgba(0, 230, 118, 0.20)');
  const grid = getCssVar('--border') || '#1f2937';
  const text = getCssVar('--text') || '#e5e7eb';
  window.__monthlyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '当月累计盈亏',
        data,
        backgroundColor: data.map(v => v >= 0 ? gradUp : gradDown)
      }]
    },
    options: {
      responsive: true,
      scales: { x: { ticks: { color: text }, grid: { color: grid } }, y: { beginAtZero: true, ticks: { color: text }, grid: { color: grid } } },
      plugins: {
        legend: { display: false },
        zoom: { zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }, pan: { enabled: true, mode: 'x' } }
      },
      onClick: (evt) => {
        // 修改为点击整个纵向区域即可选择月份
        const rect = window.__monthlyChart.canvas.getBoundingClientRect();
        const x = evt.clientX - rect.left;
        const chartArea = window.__monthlyChart.chartArea;
        const xAxis = window.__monthlyChart.scales.x;
        
        // 检查点击是否在图表区域内
        if (x >= chartArea.left && x <= chartArea.right) {
          // 计算点击位置对应的索引
          const index = Math.floor((x - chartArea.left) / ((chartArea.right - chartArea.left) / labels.length));
          if (index >= 0 && index < labels.length) {
            const month = labels[index];
            setSelectedMonth(month);
          }
        }
      }
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
    setupFontSizeControl();
    const months = await fetchJSON('data/monthly.json');
    const trades = await fetchJSON('data/trades.json');
    const positions = await fetchJSON('data/positions.json').catch(() => []);
    const posTs = await fetchJSON('data/positions_timeseries.json').catch(() => []);
    window.__months = months;
    window.__tradesAll = trades;
    renderMonthlyChart(months);
    renderMonthsList(months);
    setupThemeSelector(() => {
      renderMonthlyChart(months);
      renderDailyTimeline(window.__tradesAll, window.__selectedMonth);
      renderPositionsDonut(positions, window.__selectedMonth);
      renderProfitTrend(trades);
    });
    
    // 添加总体概览
    renderOverallSummary(months, trades);
    
    // 默认选中最后一个月份
    const defaultMonth = months.length ? months[months.length - 1].month : undefined;
    setSelectedMonth(defaultMonth);

    const stocks = await fetchJSON('data/stocks.json');
    renderStocksTable(stocks, 'total_pnl', 'desc');

    renderPositionsDonut(positions, defaultMonth);
    renderProfitTrend(trades);
    bindModalClose();
  } catch (e) {
    console.error(e);
    alert('加载数据失败，请确认已生成 data/*.json');
  }
}

init();

// ----- New components -----

function renderOverallSummary(months, trades) {
  const box = document.getElementById('overallSummaryGrid');
  if (!box) return;
  
  const totalPnl = months.reduce((sum, m) => sum + Number(m.total_pnl || 0), 0);
  const totalTrades = trades.length;
  const wins = trades.filter(t => Number(t.pnl || 0) > 0).length;
  const losses = trades.filter(t => Number(t.pnl || 0) < 0).length;
  const winRate = totalTrades > 0 ? (wins / totalTrades * 100) : 0;
  const plRatio = losses > 0 ? (wins / losses) : wins;
  const activeStocks = new Set(trades.map(t => t.code)).size;
  
  box.innerHTML = `
    <div class="k"><div class="t">总盈亏（元）</div><div class="v">${fmtPnl(totalPnl)}</div></div>
    <div class="k"><div class="t">总交易笔数</div><div class="v">${totalTrades}</div></div>
    <div class="k"><div class="t">总胜率</div><div class="v">${winRate.toFixed(2)}%</div></div>
    <div class="k"><div class="t">盈亏比例（笔数）</div><div class="v">${(plRatio || 0).toFixed(2)}</div></div>
    <div class="k"><div class="t">交易股票数量</div><div class="v">${activeStocks}</div></div>
  `;
}

function setSelectedMonth(m) {
  window.__selectedMonth = m;
  if (m) {
    renderTopSummary(m, window.__tradesAll);
    renderDailyTimeline(window.__tradesAll, m);
    // 更新持仓环形图以显示选定月份的数据
    renderPositionsDonut(window.__positions, m);
    
    // 高亮显示选中的月份
    const monthElements = document.querySelectorAll('.month .head .m');
    monthElements.forEach(el => {
      if (el.textContent === m) {
        el.parentElement.parentElement.classList.add('selected');
      } else {
        el.parentElement.parentElement.classList.remove('selected');
      }
    });
  }
}

function renderTopSummary(month, trades) {
  const box = document.getElementById('topSummaryGrid');
  if (!box) return;
  const list = (trades || []).filter(t => (t.sell_date || t.sell_dt || '').slice(0, 7) === month);
  const buyCost = list.reduce((a, t) => a + Number(t.buy_cost_net || 0), 0);
  const sellIn = list.reduce((a, t) => a + Number(t.sell_proceeds_net || 0), 0);
  const turnover = buyCost + sellIn; // 近似：当月累计成交额
  const wins = list.filter(t => Number(t.pnl || 0) > 0).length;
  const losses = list.filter(t => Number(t.pnl || 0) < 0).length;
  const plRatio = losses > 0 ? (wins / losses) : wins; // 盈亏比例（笔数）
  const activeStocks = new Set(list.map(t => t.code)).size;
  box.innerHTML = `
    <div class="k"><div class="t">当月交易总额</div><div class="v">${turnover.toFixed(2)}</div></div>
    <div class="k"><div class="t">盈亏比例（笔数）</div><div class="v">${(plRatio || 0).toFixed(2)}</div></div>
    <div class="k"><div class="t">活跃股票数量</div><div class="v">${activeStocks}</div></div>
  `;
}

function renderDailyTimeline(trades, month) {
  const ctx = document.getElementById('dailyTimeline');
  if (!ctx) return;
  if (window.__dailyChart) { window.__dailyChart.destroy(); }
  const grid = getCssVar('--border') || '#1f2937';
  const text = getCssVar('--text') || '#e5e7eb';
  const up = getCssVar('--up') || 'rgba(255, 82, 82, 0.8)';
  const down = getCssVar('--down') || 'rgba(0, 230, 118, 0.8)';
  const gctx = ctx.getContext('2d');
  const gradUp = gctx.createLinearGradient(0, 0, 0, ctx.height);
  gradUp.addColorStop(0, 'rgba(255, 82, 82, 0.85)');
  gradUp.addColorStop(1, 'rgba(255, 82, 82, 0.20)');
  const gradDown = gctx.createLinearGradient(0, 0, 0, ctx.height);
  gradDown.addColorStop(0, 'rgba(0, 230, 118, 0.85)');
  gradDown.addColorStop(1, 'rgba(0, 230, 118, 0.20)');
  const list = (trades || []).filter(t => (t.sell_date || t.sell_dt || '').slice(0, 7) === month);
  const map = new Map();
  list.forEach(t => {
    const d = (t.sell_date || t.sell_dt || '').slice(0, 10);
    const pnl = Number(t.pnl || 0);
    map.set(d, (map.get(d) || 0) + pnl);
  });
  const labels = Array.from(map.keys()).sort((a, b) => a.localeCompare(b));
  const data = labels.map(d => map.get(d));
  window.__dailyChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: '当日盈亏（元）', data, backgroundColor: data.map(v => v >= 0 ? gradUp : gradDown) }] },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        zoom: { zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }, pan: { enabled: true, mode: 'x' } }
      },
      scales: { x: { ticks: { color: text }, grid: { color: grid } }, y: { beginAtZero: true, ticks: { color: text }, grid: { color: grid } } },
      onClick: (evt) => {
        const points = window.__dailyChart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
        if (points && points.length) {
          const i = points[0].index;
          const day = labels[i];
          showDayDetails(day, trades);
        }
      }
    }
  });
}

function renderPositionsDonut(positions, selectedMonth) {
  const ctx = document.getElementById('positionsDonut');
  if (!ctx) return;
  if (window.__posDonut) { window.__posDonut.destroy(); }
  
  // 保存全局引用以便月份切换时使用
  window.__positions = positions;
  
  // 如果没有选定月份，则不显示数据
  if (!selectedMonth || !positions || !positions.length) return;
  
  // 过滤出选定月份的持仓数据
  const monthPositions = positions.filter(p => {
    const posDate = p.date || '';
    return posDate.startsWith(selectedMonth);
  });
  
  // 如果该月没有持仓数据，则不显示
  if (!monthPositions.length) return;
  
  // 按股票代码分组，取每个股票在该月的最后一条记录
  const stockMap = new Map();
  monthPositions.forEach(p => {
    const key = p.code;
    if (!stockMap.has(key) || p.date > stockMap.get(key).date) {
      stockMap.set(key, p);
    }
  });
  
  const filteredPositions = Array.from(stockMap.values()).filter(p => Number(p.position_qty || 0) > 0);
  
  // 如果没有有效持仓，则不显示
  if (!filteredPositions.length) return;
  
  const labels = filteredPositions.map(p => `${p.code}${p.name ? ' '+p.name : ''}`);
  const data = filteredPositions.map(p => Math.max(0, Number(p.position_qty || 0)));
  const accent = getCssVar('--accent') || '#4FC3F7';
  const grid = getCssVar('--border') || '#1f2937';
  const text = getCssVar('--text') || '#e5e7eb';
  const colors = labels.map((_, i) => `hsla(${(i*37)%360}, 70%, 60%, 0.75)`);
  
  window.__posDonut = new Chart(ctx, {
    type: 'doughnut',
    data: { labels, datasets: [{ label: '持仓股数占比', data, backgroundColor: colors, borderColor: grid }] },
    options: { 
      responsive: true, 
      plugins: { 
        legend: { labels: { color: text } }, 
        tooltip: { callbacks: { label: (c) => `${c.label}: ${c.parsed.toLocaleString()} 股` } },
        title: {
          display: true,
          text: `${selectedMonth} 持仓分布`,
          color: text,
          font: { size: 14 }
        }
      } 
    }
  });
}

function renderProfitTrend(ts) {
  const ctx = document.getElementById('profitTrend');
  if (!ctx || !ts || !ts.length) return;
  if (window.__profitTrend) { window.__profitTrend.destroy(); }
  
  // 按日期对交易进行分组，计算每日累计盈亏
  const dailyPnl = {};
  let cumulativePnl = 0;
  
  ts.forEach(item => {
    if (item.pnl) {
      const date = item.sell_date || item.sell_dt;
      if (date && !dailyPnl[date]) {
        dailyPnl[date] = 0;
      }
      if (date) {
        dailyPnl[date] += Number(item.pnl);
      }
    }
  });
  
  // 按日期排序并计算累计盈亏
  const sortedDates = Object.keys(dailyPnl).sort();
  const labels = [];
  const data = [];
  
  sortedDates.forEach(date => {
    cumulativePnl += dailyPnl[date];
    labels.push(date);
    data.push(cumulativePnl);
  });
  
  const gctx = ctx.getContext('2d');
  const accent = getCssVar('--accent') || '#4FC3F7';
  const grid = getCssVar('--border') || '#1f2937';
  const text = getCssVar('--text') || '#e5e7eb';
  const grad = gctx.createLinearGradient(0, 0, 0, ctx.height);
  grad.addColorStop(0, 'rgba(79, 195, 247, 0.35)');
  grad.addColorStop(1, 'rgba(79, 195, 247, 0.05)');
  
  window.__profitTrend = new Chart(ctx, {
    type: 'line',
    data: { 
      labels, 
      datasets: [{ 
        label: '累计盈亏（元）', 
        data, 
        borderColor: accent, 
        backgroundColor: grad, 
        fill: true 
      }] 
    },
    options: { 
      responsive: true, 
      plugins: { 
        legend: { display: false }, 
        zoom: { 
          zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }, 
          pan: { enabled: true, mode: 'x' } 
        } 
      }, 
      scales: { 
        x: { ticks: { color: text }, grid: { color: grid } }, 
        y: { ticks: { color: text }, grid: { color: grid } } 
      } 
    }
  });
}

function bindModalClose() {
  const modal = document.getElementById('dayModal');
  const btn = document.getElementById('dayModalClose');
  if (btn && modal) {
    btn.addEventListener('click', () => modal.classList.remove('show'));
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('show'); });
  }
}

function showDayDetails(day, trades) {
  const modal = document.getElementById('dayModal');
  const body = document.getElementById('dayModalBody');
  const title = document.getElementById('dayModalTitle');
  if (!modal || !body || !title) return;
  title.textContent = `当日交易详情：${day}`;
  const list = (trades || []).filter(t => (t.sell_date || t.sell_dt || '').slice(0, 10) === day);
  const rows = list.map(t => `
    <tr>
      <td>${t.sell_date || t.sell_dt}</td>
      <td><a href="stock.html?code=${encodeURIComponent(t.code)}">${t.code}</a></td>
      <td>${t.name || ''}</td>
      <td>${t.qty}</td>
      <td>${(t.avg_buy_price || 0).toFixed(4)}</td>
      <td>${(t.avg_sell_price || 0).toFixed(4)}</td>
      <td>${(t.buy_cost_net || 0).toFixed(2)}</td>
      <td>${(t.sell_proceeds_net || 0).toFixed(2)}</td>
      <td>${(t.fees_total || 0).toFixed(2)}</td>
      <td>${(t.pnl || 0).toFixed(2)}</td>
    </tr>
  `).join('');
  body.innerHTML = `
    <table class="table">
      <thead>
        <tr><th>日期</th><th>代码</th><th>名称</th><th>数量</th><th>均买价</th><th>均卖价</th><th>买净支出</th><th>卖净收入</th><th>费用</th><th>盈亏</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  modal.classList.add('show');
}