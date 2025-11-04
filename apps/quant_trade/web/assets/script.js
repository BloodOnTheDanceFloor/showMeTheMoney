/* 简单技术指标实现（近似） */
function sma(arr, period) {
  const out = new Array(arr.length).fill(NaN);
  let sum = 0;
  for (let i = 0; i < arr.length; i++) {
    sum += arr[i];
    if (i >= period) sum -= arr[i - period];
    if (i >= period - 1) out[i] = sum / period;
  }
  return out;
}

function ema(arr, span) {
  const out = new Array(arr.length).fill(NaN);
  const alpha = 2 / (span + 1);
  out[0] = arr[0];
  for (let i = 1; i < arr.length; i++) {
    out[i] = alpha * arr[i] + (1 - alpha) * out[i - 1];
  }
  return out;
}

function rsi(arr, period) {
  const out = new Array(arr.length).fill(50);
  for (let i = 1; i < arr.length; i++) {
    const diff = arr[i] - arr[i - 1];
    const up = Math.max(diff, 0);
    const down = Math.max(-diff, 0);
    const start = Math.max(0, i - period + 1);
    let sumUp = 0, sumDown = 0;
    for (let j = start; j <= i; j++) {
      const d = arr[j] - (j ? arr[j - 1] : arr[j]);
      sumUp += Math.max(d, 0);
      sumDown += Math.max(-d, 0);
    }
    const rs = sumDown === 0 ? 1 : sumUp / sumDown;
    out[i] = 100 - (100 / (1 + rs));
  }
  return out;
}

function macd(close, fast = 12, slow = 26, signal = 9) {
  const macdLine = ema(close, fast).map((v, i) => v - ema(close, slow)[i]);
  const signalLine = ema(macdLine, signal);
  const hist = macdLine.map((v, i) => v - signalLine[i]);
  return { macd: macdLine, signal: signalLine, hist };
}

function atr(high, low, close, period) {
  const tr = new Array(close.length).fill(NaN);
  for (let i = 0; i < close.length; i++) {
    const prevClose = i > 0 ? close[i - 1] : close[i];
    tr[i] = Math.max(
      high[i] - low[i],
      Math.abs(high[i] - prevClose),
      Math.abs(low[i] - prevClose)
    );
  }
  return sma(tr, period).map((v, i) => Number.isFinite(v) ? v : tr.reduce((a, b) => a + b, 0) / tr.length);
}

function generateSignal(df, cfg) {
  const { ma20, ma60, ma120, rsiLow, rsiHigh, volMult } = cfg;
  const close = df.close, high = df.high, low = df.low, vol = df.volume;
  const ma20v = sma(close, ma20), ma60v = sma(close, ma60), ma120v = sma(close, ma120);
  const rsiv = rsi(close, 14);
  const m = macd(close);
  const vol120 = sma(vol, 120);
  const signal = close.map((c, i) => (
    (c > ma20v[i]) && (ma20v[i] > ma60v[i]) && (ma60v[i] > ma120v[i]) &&
    (m.macd[i] > m.signal[i]) && (m.hist[i] > 0) && (m.hist[i] > (i ? m.hist[i - 1] : m.hist[i])) &&
    (rsiv[i] > rsiLow) && (rsiv[i] < rsiHigh) &&
    (vol[i] > (vol120[i] || Infinity) * volMult)
  ));
  return { ma20: ma20v, ma60: ma60v, ma120: ma120v, rsi: rsiv, macd: m, vol120, signal };
}

function runBacktest(df, ind, cfg) {
  const { atrSL, atrTP, posRatio } = cfg;
  const n = df.close.length;
  const atr14 = atr(df.high, df.low, df.close, 14);
  let cash = 1_000_000, pos = 0, entry = 0;
  const nav = new Array(n).fill(NaN);
  for (let i = 0; i < n; i++) {
    const price = df.close[i];
    if (pos > 0) {
      const sl = entry - atrSL * atr14[i];
      const tp = entry + atrTP * atr14[i];
      if (df.low[i] <= sl) { cash = pos * sl; pos = 0; }
      else if (df.high[i] >= tp) { cash = pos * tp; pos = 0; }
    }
    if (pos === 0 && ind.signal[i]) {
      pos = (1_000_000 * posRatio) / price;
      entry = price;
      cash -= 1_000_000 * posRatio;
    }
    nav[i] = cash + (pos > 0 ? pos * price : 0);
  }
  return nav.map(v => v / 1_000_000);
}

/* 数据获取与可视化 */
const state = {
  cache: new Map(),
  chart: null
};

function fmtDate(dt) {
  const y = dt.getFullYear().toString();
  const m = String(dt.getMonth() + 1).padStart(2, '0');
  const d = String(dt.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

async function fetchKline(base, symbol, startYmd, endYmd, signal) {
  const key = `${base}|${symbol}|${startYmd}|${endYmd}`;
  if (state.cache.has(key)) return state.cache.get(key);
  const start = `${startYmd.substring(0,4)}-${startYmd.substring(4,6)}-${startYmd.substring(6)}`;
  const end = `${endYmd.substring(0,4)}-${endYmd.substring(4,6)}-${endYmd.substring(6)}`;
  const url = `${base}/stocks/${symbol.toLowerCase()}/kline?start_date=${start}&end_date=${end}`;
  const controller = new AbortController();
  if (signal) signal.addEventListener('abort', () => controller.abort());
  const t0 = performance.now();
  let resp = await fetch(url, { signal: controller.signal });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const json = await resp.json();
  const records = Array.isArray(json) ? json : json.data;
  const t1 = performance.now();
  if ((t1 - t0) > 2000) console.warn('数据加载超过2秒：', (t1 - t0).toFixed(0), 'ms');
  const df = {
    date: records.map(r => new Date(r.date)),
    open: records.map(r => +r.open || 0),
    high: records.map(r => +r.high || 0),
    low: records.map(r => +r.low || 0),
    close: records.map(r => +r.close || 0),
    volume: records.map(r => +r.volume || 0),
  };
  state.cache.set(key, df);
  return df;
}

function renderChart(df, nav) {
  const ctx = document.getElementById('chart');
  const labels = df.date.map(d => fmtDate(d));
  const dataClose = df.close;
  const dataNav = nav || [];
  const ds = [
    { label: '收盘', data: dataClose, borderColor: '#1976d2', tension: 0.1 },
  ];
  if (dataNav.length) ds.push({ label: '净值', data: dataNav, yAxisID: 'y1', borderColor: '#43a047', tension: 0.1 });

  const cfg = {
    type: 'line',
    data: { labels, datasets: ds },
    options: {
      responsive: true,
      interaction: { mode: 'nearest', intersect: false },
      plugins: {
        zoom: { zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' } }
      },
      scales: {
        y: { position: 'left' },
        y1: { position: 'right', grid: { drawOnChartArea: false } }
      }
    }
  };
  if (state.chart) state.chart.destroy();
  state.chart = new Chart(ctx, cfg);
}

function getCfg() {
  return {
    ma20: +document.getElementById('ma20').value,
    ma60: +document.getElementById('ma60').value,
    ma120: +document.getElementById('ma120').value,
    rsiLow: +document.getElementById('rsiLow').value,
    rsiHigh: +document.getElementById('rsiHigh').value,
    volMult: +document.getElementById('volMult').value,
    atrSL: +document.getElementById('atrSL').value,
    atrTP: +document.getElementById('atrTP').value,
    posRatio: +document.getElementById('posRatio').value,
  };
}

async function onLoad() {
  const base = document.getElementById('apiBase').value.trim();
  const code = document.getElementById('code').value.trim();
  const start = document.getElementById('start').value.trim();
  const end = document.getElementById('end').value.trim();
  const df = await fetchKline(base, normalize(code), start, end);
  renderChart(df);
}

function normalize(code) {
  code = code.trim().toLowerCase();
  if (code.includes('.')) {
    const [num, suf] = code.split('.');
    if (suf === 'sh') return `sh${num}`;
    if (suf === 'sz') return `sz${num}`;
    if (suf === 'bj') return `bj${num}`;
  }
  return code;
}

async function onBacktest() {
  const base = document.getElementById('apiBase').value.trim();
  const code = document.getElementById('code').value.trim();
  const start = document.getElementById('start').value.trim();
  const end = document.getElementById('end').value.trim();
  const cfg = getCfg();
  const df = await fetchKline(base, normalize(code), start, end);
  const ind = generateSignal(df, cfg);
  const nav = runBacktest(df, ind, cfg);
  renderChart(df, nav);
}

async function onScan() {
  const base = document.getElementById('apiBase').value.trim();
  const cfg = getCfg();
  const codes = [
    '300378.SZ','300073.SZ','002629.SZ','600089.SH','600121.SH','000426.SZ','603993.SH','600489.SH','002460.SZ','000776.SZ','518880.SH','002594.SZ','204001.SH','513010.SH'
  ];
  const date = document.getElementById('end').value.trim();
  const start = (() => {
    const y = +date.substring(0,4), m = +date.substring(4,6), d = +date.substring(6);
    const dt = new Date(y, m-1, d);
    dt.setDate(dt.getDate() - 200);
    return `${dt.getFullYear()}${String(dt.getMonth()+1).padStart(2,'0')}${String(dt.getDate()).padStart(2,'0')}`;
  })();
  const tbody = document.querySelector('#scanTable tbody');
  tbody.innerHTML = '';
  const tasks = codes.map(async c => {
    try {
      const df = await fetchKline(base, normalize(c), start, date);
      const ind = generateSignal(df, cfg);
      const i = df.close.length - 1;
      if (ind.signal[i]) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${c}</td><td>${df.close[i].toFixed(2)}</td><td>${ind.rsi[i].toFixed(2)}</td><td>${atr(df.high, df.low, df.close, 14)[i].toFixed(2)}</td>`;
        tbody.appendChild(tr);
      }
    } catch (e) {
      console.warn('扫描失败:', c, e);
    }
  });
  await Promise.all(tasks);
}

async function onTrade() {
  const t0 = performance.now();
  // 模拟下单动作：更新UI
  await new Promise(resolve => setTimeout(resolve, 50));
  const t1 = performance.now();
  const lat = Math.round(t1 - t0);
  document.getElementById('tradeLatency').textContent = `指令延迟 ${lat}ms`;
}

function onPing() {
  const base = document.getElementById('apiBase').value.trim();
  const status = document.getElementById('pingStatus');
  const t0 = performance.now();
  const url = `${base}/stocks/sh600000/kline?start_date=2025-10-01&end_date=2025-10-02`;
  fetch(url).then(() => {
    const t = Math.round(performance.now() - t0);
    status.textContent = `可访问（${t}ms）`;
  }).catch(() => {
    status.textContent = '不可访问';
  });
}

document.getElementById('loadBtn').addEventListener('click', onLoad);
document.getElementById('backtestBtn').addEventListener('click', onBacktest);
document.getElementById('scanBtn').addEventListener('click', onScan);
document.getElementById('tradeBtn').addEventListener('click', onTrade);
document.getElementById('pingBtn').addEventListener('click', onPing);
/* --- 批量分析与评分 --- */
function maxDrawdown(nav) {
  let peak = -Infinity, mdd = 0;
  for (let i = 0; i < nav.length; i++) {
    const v = nav[i];
    if (!Number.isFinite(v)) continue;
    peak = Math.max(peak, v);
    if (peak > 0) mdd = Math.max(mdd, (peak - v) / peak);
  }
  return mdd;
}

function annualizedReturn(nav, dates) {
  const vals = nav.filter(Number.isFinite);
  if (!vals.length) return 0;
  const start = dates[0], end = dates[dates.length - 1];
  const days = Math.max(1, (end - start) / (1000 * 3600 * 24));
  const final = vals[vals.length - 1];
  const ann = Math.pow(final, 365 / days) - 1;
  if (!Number.isFinite(ann)) return 0;
  return ann;
}

function scoreFromPerf(ret, mdd) {
  const reward = ret / (mdd + 1e-9);
  const s = 50 + 50 * Math.tanh(reward);
  return Math.max(0, Math.min(100, s));
}

function signalsTrend(df, cfg) {
  return generateSignal(df, cfg);
}

function signalsStrength(df, cfg) {
  const rsiv = rsi(df.close, 14);
  const ma20v = sma(df.close, cfg.ma20 || 20);
  const signal = rsiv.map((v, i) => v > (cfg.rsiHigh || 60) && df.close[i] > ma20v[i]);
  return { rsi: rsiv, ma20: ma20v, signal };
}

function signalsVolume(df, cfg) {
  const volMA = sma(df.volume, 120);
  const ma20v = sma(df.close, 20);
  const signal = df.volume.map((v, i) => v > (volMA[i] || Infinity) * (cfg.volMult || 1.2) && df.close[i] > ma20v[i]);
  return { volMA, ma20: ma20v, signal };
}

function signalsBreakout(df, n = 20) {
  const highs = df.close;
  const signal = highs.map((v, i) => {
    const start = Math.max(0, i - n + 1);
    const prevHigh = Math.max(...highs.slice(start, i));
    return i > 0 && v > prevHigh;
  });
  return { signal };
}

function adviceFromScore(total) {
  if (total >= 75) return '谨慎买入';
  if (total >= 60) return '观察/轻仓';
  if (total >= 45) return '观望';
  return '回避/减仓';
}

async function analyzeOneStock(base, code, start, end, cfg, enabled) {
  const df = await fetchKline(base, normalize(code), start, end);
  const last = df.close[df.close.length - 1];
  const results = {};
  const strategists = [];
  if (enabled.trend) strategists.push(['trend', signalsTrend(df, cfg)]);
  if (enabled.strength) strategists.push(['strength', signalsStrength(df, cfg)]);
  if (enabled.volume) strategists.push(['volume', signalsVolume(df, cfg)]);
  if (enabled.breakout) strategists.push(['breakout', signalsBreakout(df, 20)]);
  const rets = [];
  for (const [name, ind] of strategists) {
    const nav = runBacktest(df, ind, cfg);
    const ret = (nav.filter(Number.isFinite).pop() || 1) - 1;
    const mdd = maxDrawdown(nav);
    const ann = annualizedReturn(nav, df.date);
    const score = scoreFromPerf(ann, mdd);
    results[name] = { ret, mdd, ann, score };
    rets.push(Math.max(0, ann));
  }
  const sumPos = rets.reduce((a, b) => a + b, 0);
  const weights = rets.map(r => (sumPos > 0 ? r / sumPos : 1 / rets.length));
  const scores = strategists.map(([name]) => results[name].score);
  const total = scores.reduce((a, s, i) => a + s * (weights[i] || 0), 0);
  return { last, results, total };
}

function parseCodes(text) {
  return text.split(/\n|\r|,|;|\s+/).map(s => s.trim()).filter(Boolean);
}

async function onMulti() {
  const base = document.getElementById('apiBase').value.trim();
  const start = document.getElementById('start').value.trim();
  const end = document.getElementById('end').value.trim();
  const cfg = getCfg();
  const enabled = {
    trend: document.getElementById('stTrend').checked,
    strength: document.getElementById('stStrength').checked,
    volume: document.getElementById('stVolume').checked,
    breakout: document.getElementById('stBreakout').checked,
  };
  const codesText = document.getElementById('codes').value.trim();
  const codes = parseCodes(codesText);
  const tbody = document.querySelector('#scoreTable tbody');
  tbody.innerHTML = '';
  for (const code of codes) {
    try {
      const r = await analyzeOneStock(base, code, start, end, cfg, enabled);
      const t = r.results;
      const tr = document.createElement('tr');
      const trendS = t.trend ? t.trend.score.toFixed(1) : '-';
      const strengthS = t.strength ? t.strength.score.toFixed(1) : '-';
      const volumeS = t.volume ? t.volume.score.toFixed(1) : '-';
      const breakoutS = t.breakout ? t.breakout.score.toFixed(1) : '-';
      const totalS = r.total.toFixed(1);
      tr.innerHTML = `<td>${code}</td><td>${r.last.toFixed(2)}</td><td>${trendS}</td><td>${strengthS}</td><td>${volumeS}</td><td>${breakoutS}</td><td>${totalS}</td><td>${adviceFromScore(r.total)}</td>`;
      tbody.appendChild(tr);
    } catch (e) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${code}</td><td colspan="6">加载失败</td><td>—</td>`;
      tbody.appendChild(tr);
      console.warn('分析失败:', code, e);
    }
  }
}

document.getElementById('multiBtn').addEventListener('click', onMulti);