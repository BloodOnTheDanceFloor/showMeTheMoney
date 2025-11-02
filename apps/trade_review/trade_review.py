import os
import io
import base64
import argparse
from datetime import datetime
from typing import List, Dict, Tuple

import pandas as pd
import numpy as np
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt


def _find_header_row(df: pd.DataFrame) -> int:
    """在无表头DataFrame中查找包含关键列的表头行索引。未找到返回-1。"""
    key_candidates = (
        {'证券代码', '成交日期', '成交数量', '成交价格'},
        {'证券代码', '申报日期', '成交数量', '成交价格'},
        {'证券代码', '成交日期', '成交金额', '清算金额'},
        {'证券代码', '申报日期', '成交金额', '清算金额'},
    )
    max_scan = min(len(df), 100)
    for i in range(max_scan):
        row_vals = set([str(v).strip() for v in df.iloc[i].tolist()])
        if any(k.issubset(row_vals) for k in key_candidates):
            return i
    return -1


def load_trade_excel(path: str) -> pd.DataFrame:
    """读取成交Excel，抽取并标准化字段。"""
    raw = pd.read_excel(path, header=None, engine='openpyxl')
    hdr_idx = _find_header_row(raw)
    if hdr_idx < 0:
        raise RuntimeError('无法定位表头行（未发现包含“证券代码/成交日期”等关键列的行）')
    header = raw.iloc[hdr_idx].astype(str).str.strip().tolist()
    df = raw.iloc[hdr_idx + 1:].copy()
    df.columns = header

    # 目标列映射（存在则选择，不存在则置空）
    col = df.columns
    def pick(*names):
        for n in names:
            if n in col:
                return n
        return None

    c_code = pick('证券代码')
    c_name = pick('证券名称')
    c_date = pick('成交日期', '申报日期')
    c_time = pick('成交时间', '申报时间')
    c_qty = pick('成交数量')
    c_price = pick('成交价格')
    c_amt = pick('成交金额')
    c_net = pick('清算金额')
    c_fee_comm = pick('佣金')
    c_fee_stamp = pick('印花税')
    c_fee_transfer = pick('过户费')
    c_fee_other = pick('其他费用')
    c_remark = pick('备注')

    if not all([c_code, c_date, c_qty, c_price]):
        raise RuntimeError('表头缺少必要列（证券代码/成交日期/成交数量/成交价格）')

    out = pd.DataFrame({
        'code': df[c_code].astype(str).str.strip(),
        'name': df[c_name].astype(str).str.strip() if c_name else '',
        'date': pd.to_datetime(df[c_date].astype(str).str.strip(), errors='coerce'),
        'time': df[c_time].astype(str).str.strip() if c_time else '',
        'qty': pd.to_numeric(df[c_qty], errors='coerce'),
        'price': pd.to_numeric(df[c_price], errors='coerce'),
        'amount': pd.to_numeric(df[c_amt], errors='coerce') if c_amt else np.nan,
        'net_amount': pd.to_numeric(df[c_net], errors='coerce') if c_net else np.nan,
        'fee_commission': pd.to_numeric(df[c_fee_comm], errors='coerce') if c_fee_comm else 0.0,
        'fee_stamp': pd.to_numeric(df[c_fee_stamp], errors='coerce') if c_fee_stamp else 0.0,
        'fee_transfer': pd.to_numeric(df[c_fee_transfer], errors='coerce') if c_fee_transfer else 0.0,
        'fee_other': pd.to_numeric(df[c_fee_other], errors='coerce') if c_fee_other else 0.0,
        'remark': df[c_remark].astype(str).str.strip() if c_remark else ''
    })

    out['fee_total'] = out[['fee_commission', 'fee_stamp', 'fee_transfer', 'fee_other']].fillna(0).sum(axis=1)
    # 买卖方向判断
    def infer_side(row):
        rmk = str(row['remark']) if pd.notna(row['remark']) else ''
        if '买入' in rmk:
            return '买入'
        if '卖出' in rmk:
            return '卖出'
        q = row['qty']
        if pd.notna(q):
            return '买入' if q > 0 else '卖出'
        net = row['net_amount']
        if pd.notna(net):
            return '买入' if net < 0 else '卖出'
        return '未知'

    out['side'] = out.apply(infer_side, axis=1)

    # 合并日期与时间为datetime，用于排序
    def parse_dt(d, t):
        if pd.isna(d):
            return pd.NaT
        t = (t or '').strip()
        if not t:
            return pd.to_datetime(d)
        try:
            if len(t) == 6 and t.isdigit():
                hh, mm, ss = int(t[0:2]), int(t[2:4]), int(t[4:6])
                return datetime(d.year, d.month, d.day, hh, mm, ss)
            return pd.to_datetime(f"{d.date()} {t}")
        except Exception:
            return pd.to_datetime(d)

    out['dt'] = [parse_dt(d, t) for d, t in zip(out['date'], out['time'])]

    # 仅保留A股常见代码，剔除指定登记/回购/GC等非股票交易
    def is_stock(code, name, remark):
        code = str(code)
        if len(code) != 6 or not code.isdigit():
            return False
        if code == '799999':
            return False
        nm = str(name)
        rmk = str(remark)
        if nm.startswith('GC') or '指定登记' in nm or '指定登记' in rmk:
            return False
        # 常见A股前缀：000/001/002/003/300/301/600/601/603/605等
        return code[0:3] in {
            '000', '001', '002', '003', '300', '301', '600', '601', '603', '605'
        }

    out = out[out.apply(lambda r: is_stock(r['code'], r['name'], r['remark']), axis=1)].copy()
    out = out.dropna(subset=['code', 'date', 'qty', 'price'])
    out = out.sort_values(['code', 'dt']).reset_index(drop=True)
    return out


def fifo_match_and_pnl(df: pd.DataFrame) -> pd.DataFrame:
    """对每只股票进行FIFO撮合，生成以卖出为单位的已实现交易记录。"""
    records: List[Dict] = []

    for code, g in df.groupby('code', sort=False):
        g = g.sort_values('dt')
        name = g['name'].iloc[0]
        lots: List[Dict] = []  # 买入持仓队列

        for _, row in g.iterrows():
            side = row['side']
            qty = float(row['qty']) if pd.notna(row['qty']) else 0.0
            price = float(row['price']) if pd.notna(row['price']) else np.nan
            net = float(row['net_amount']) if pd.notna(row['net_amount']) else np.nan
            amount = float(row['amount']) if pd.notna(row['amount']) else np.nan
            fee_total = float(row['fee_total']) if pd.notna(row['fee_total']) else 0.0
            dt = row['dt']

            if side == '买入':
                # 买入净支出（若清算金额缺失则使用 成交金额 + 费用）
                if pd.isna(net):
                    net_out = (amount if pd.notna(amount) else price * abs(qty)) + fee_total
                    net = -abs(net_out)
                # 存入队列（以正数表达剩余数量）
                lots.append({
                    'qty_remain': abs(qty),
                    'orig_qty': abs(qty),
                    'price': price,
                    'buy_dt': dt,
                    'net_amount': float(net),  # 预计为负值（现金流流出）
                    'fee_total': fee_total,
                })
            elif side == '卖出':
                sell_qty = abs(qty)
                if pd.isna(net):
                    net_in = (amount if pd.notna(amount) else price * sell_qty) - fee_total
                    net = abs(net_in)

                qty_left = sell_qty
                matched_cost_net = 0.0
                matched_fee_buy = 0.0
                weighted_buy_price = 0.0
                weighted_buy_days = 0.0
                total_matched_qty = 0.0

                # FIFO撮合
                while qty_left > 1e-9 and len(lots) > 0:
                    lot = lots[0]
                    take = min(qty_left, lot['qty_remain'])
                    # 按数量比例分摊该买入的净支出与费用
                    portion_ratio = take / lot['orig_qty'] if lot['orig_qty'] > 0 else 0.0
                    buy_net_cost = -lot['net_amount'] * portion_ratio  # 转为正值成本
                    buy_fee_portion = lot['fee_total'] * portion_ratio

                    matched_cost_net += buy_net_cost
                    matched_fee_buy += buy_fee_portion
                    weighted_buy_price += lot['price'] * take
                    # 以交易日计算持仓周期
                    try:
                        sell_day = dt.date() if pd.notna(dt) else None
                        buy_day = lot['buy_dt'].date() if pd.notna(lot['buy_dt']) else None
                        days = (sell_day - buy_day).days if (sell_day and buy_day) else np.nan
                    except Exception:
                        days = np.nan
                    if pd.notna(days):
                        weighted_buy_days += float(days) * take
                    total_matched_qty += take

                    lot['qty_remain'] -= take
                    qty_left -= take
                    if lot['qty_remain'] <= 1e-9:
                        lots.pop(0)

                if total_matched_qty <= 1e-9:
                    # 无买入可匹配，跳过但记录为异常
                    records.append({
                        'code': code, 'name': name,
                        'sell_dt': dt, 'sell_date': row['date'],
                        'qty': sell_qty, 'avg_buy_price': np.nan,
                        'avg_sell_price': price, 'buy_cost_net': 0.0,
                        'sell_proceeds_net': net, 'fees_total': fee_total,
                        'pnl': net, 'ret_pct': np.nan, 'hold_days': np.nan
                    })
                    continue

                avg_buy_price = weighted_buy_price / total_matched_qty if total_matched_qty > 0 else np.nan
                buy_cost_net_total = matched_cost_net
                sell_proceeds_net = net  # 该卖出单的净入金

                pnl = sell_proceeds_net - buy_cost_net_total
                ret_pct = pnl / buy_cost_net_total if buy_cost_net_total > 1e-9 else np.nan
                avg_hold_days = weighted_buy_days / total_matched_qty if total_matched_qty > 0 else np.nan

                records.append({
                    'code': code, 'name': name,
                    'sell_dt': dt, 'sell_date': row['date'],
                    'qty': total_matched_qty,
                    'avg_buy_price': avg_buy_price,
                    'avg_sell_price': price,
                    'buy_cost_net': buy_cost_net_total,
                    'sell_proceeds_net': sell_proceeds_net,
                    'fees_total': matched_fee_buy + fee_total,
                    'pnl': pnl, 'ret_pct': ret_pct, 'hold_days': avg_hold_days
                })
            else:
                # 未知方向，忽略
                continue

    return pd.DataFrame.from_records(records)


def _max_drawdown(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    cum = series.cumsum()
    peak = cum.expanding().max()
    dd = (peak - cum) / peak.replace(0, np.nan)
    dd = dd.replace([np.inf, -np.inf], np.nan).fillna(0)
    return float(dd.max())


def summarize(trades: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    trades = trades.copy()
    trades['is_win'] = trades['pnl'] > 0

    stock_rows = []
    for code, g in trades.groupby('code'):
        g = g.sort_values('sell_dt')
        name = g['name'].iloc[0]
        win_rate = (g['is_win'].mean() * 100.0) if len(g) else 0.0
        max_win = float(g['pnl'].max()) if len(g) else 0.0
        max_loss = float(g['pnl'].min()) if len(g) else 0.0
        mdd = _max_drawdown(g['pnl'])
        avg_hold = float(g['hold_days'].mean()) if len(g) else np.nan
        avg_ret_pct = float((g['ret_pct'].dropna().mean() * 100.0)) if len(g.dropna(subset=['ret_pct'])) else np.nan
        stock_rows.append({
            'code': code, 'name': name,
            'trade_count': int(len(g)),
            'win_rate_%': win_rate,
            'total_pnl': float(g['pnl'].sum()),
            'max_win': max_win,
            'max_loss': max_loss,
            'max_drawdown_%': mdd * 100.0,
            'avg_hold_days': avg_hold,
            'avg_ret_%': avg_ret_pct,
        })
    stock_summary = pd.DataFrame(stock_rows).sort_values('total_pnl', ascending=False)

    # Overall
    wins = trades[trades['pnl'] > 0]['pnl']
    losses = -trades[trades['pnl'] < 0]['pnl']
    avg_win = wins.mean() if len(wins) else np.nan
    avg_loss = losses.mean() if len(losses) else np.nan
    pl_ratio = (avg_win / avg_loss) if (pd.notna(avg_win) and pd.notna(avg_loss) and avg_loss > 0) else np.nan
    overall = pd.DataFrame([{
        'total_trades': int(len(trades)),
        'total_pnl': float(trades['pnl'].sum()),
        'win_rate_%': (trades['is_win'].mean() * 100.0) if len(trades) else 0.0,
        'avg_ret_%': float(trades['ret_pct'].dropna().mean() * 100.0) if len(trades.dropna(subset=['ret_pct'])) else np.nan,
        'avg_win': float(avg_win) if pd.notna(avg_win) else np.nan,
        'avg_loss': float(avg_loss) if pd.notna(avg_loss) else np.nan,
        'avg_win_loss_ratio': float(pl_ratio) if pd.notna(pl_ratio) else np.nan,
    }])

    return stock_summary, overall


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')


def build_visuals(trades: pd.DataFrame, stock_summary: pd.DataFrame) -> Dict[str, str]:
    imgs = {}
    # 总体权益曲线
    t = trades.sort_values('sell_dt')
    fig1 = plt.figure(figsize=(8, 3))
    ax1 = fig1.add_subplot(111)
    equity = t['pnl'].cumsum()
    ax1.plot(t['sell_dt'], equity, color='#1f77b4')
    ax1.set_title('总体权益曲线')
    ax1.set_xlabel('时间')
    ax1.set_ylabel('累计盈亏')
    ax1.grid(True, alpha=0.3)
    imgs['equity_all'] = _fig_to_base64(fig1)

    # 单笔收益率分布
    fig2 = plt.figure(figsize=(8, 3))
    ax2 = fig2.add_subplot(111)
    rp = (trades['ret_pct'].dropna() * 100.0)
    if len(rp):
        ax2.hist(rp, bins=30, color='#ff7f0e', alpha=0.8)
    ax2.set_title('单笔收益率分布（%）')
    ax2.set_xlabel('收益率%')
    ax2.set_ylabel('频数')
    ax2.grid(True, alpha=0.3)
    imgs['ret_hist'] = _fig_to_base64(fig2)

    # 各股票累计盈亏柱状
    top = stock_summary.copy()
    fig3 = plt.figure(figsize=(8, 3))
    ax3 = fig3.add_subplot(111)
    # 红涨绿跌：正为红，负为绿
    colors = ['#dc2626' if v >= 0 else '#16a34a' for v in top['total_pnl']]
    ax3.bar(top['code'].astype(str), top['total_pnl'], color=colors)
    ax3.set_title('各股票累计盈亏')
    ax3.set_xlabel('股票代码')
    ax3.set_ylabel('累计盈亏')
    ax3.grid(True, axis='y', alpha=0.3)
    imgs['pnl_bar'] = _fig_to_base64(fig3)

    return imgs


def _format_table(df: pd.DataFrame, float_cols: List[str], pct_cols: List[str]) -> str:
    df = df.copy()
    for c in float_cols:
        if c in df.columns:
            df[c] = df[c].astype(float).round(2)
    for c in pct_cols:
        if c in df.columns:
            df[c] = df[c].astype(float).round(2)
    return df.to_html(index=False, border=0, classes='table')


def generate_report_html(trades: pd.DataFrame, stock_summary: pd.DataFrame, overall: pd.DataFrame, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    imgs = build_visuals(trades, stock_summary)

    # 表格HTML
    trades_display = trades.copy()
    trades_display['sell_date'] = trades_display['sell_date'].astype(str)
    trades_display['avg_buy_price'] = trades_display['avg_buy_price'].round(4)
    trades_display['avg_sell_price'] = trades_display['avg_sell_price'].round(4)
    trades_display['ret_%'] = trades_display['ret_pct'] * 100.0
    trades_display = trades_display[[
        'code', 'name', 'sell_date', 'qty', 'avg_buy_price', 'avg_sell_price',
        'buy_cost_net', 'sell_proceeds_net', 'fees_total', 'pnl', 'ret_%', 'hold_days'
    ]]

    stock_display = stock_summary.copy()
    overall_display = overall.copy()

    tbl_trades = _format_table(trades_display, ['avg_buy_price', 'avg_sell_price', 'buy_cost_net', 'sell_proceeds_net', 'fees_total', 'pnl'], ['ret_%'])
    tbl_stock = _format_table(stock_display, ['total_pnl', 'max_win', 'max_loss', 'avg_hold_days'], ['win_rate_%', 'max_drawdown_%', 'avg_ret_%'])
    tbl_overall = _format_table(overall_display, ['total_pnl', 'avg_win', 'avg_loss'], ['win_rate_%', 'avg_ret_%', 'avg_win_loss_ratio'])

    css = """
    <style>
    body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }
    h2 { margin-top: 24px; }
    .table { width: 100%; border-collapse: collapse; }
    .table th, .table td { padding: 8px 10px; border-bottom: 1px solid #eee; }
    .table th { background: #f7f7f7; text-align: left; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 18px; }
    .chart { width: 100%; }
    .note { color: #666; font-size: 12px; }
    </style>
    """

    html = f"""
    <html>
    <head>
      <meta charset='utf-8'>
      <title>交易复盘表</title>
      {css}
    </head>
    <body>
      <h1>交易复盘表</h1>
      <div class='grid'>
        <div class='chart'><img src='data:image/png;base64,{imgs['equity_all']}' /></div>
        <div class='chart'><img src='data:image/png;base64,{imgs['ret_hist']}' /></div>
        <div class='chart'><img src='data:image/png;base64,{imgs['pnl_bar']}' /></div>
      </div>

      <h2>1. 个股交易汇总表</h2>
      {tbl_stock}

      <h2>2. 交易明细表</h2>
      {tbl_trades}

      <h2>3. 关键指标统计表</h2>
      {tbl_overall}

      <p class='note'>说明：收益率按每次卖出与其匹配买入的净支出计算；费用包含佣金、印花税、过户费与其他费用。</p>
    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def export_json_assets(trades_raw: pd.DataFrame, trades: pd.DataFrame, stock_summary: pd.DataFrame, overall: pd.DataFrame, data_dir: str):
    os.makedirs(data_dir, exist_ok=True)
    stock_dir = os.path.join(data_dir, 'stock')
    os.makedirs(stock_dir, exist_ok=True)

    # Helper: convert DataFrame to JSON-serializable list of dicts
    def df_to_records(df: pd.DataFrame) -> List[Dict]:
        recs = []
        for _, r in df.iterrows():
            obj = {}
            for k, v in r.items():
                if isinstance(v, (pd.Timestamp, datetime)):
                    obj[k] = str(v)
                elif isinstance(v, (np.floating, float)):
                    obj[k] = float(v)
                elif isinstance(v, (np.integer, int)):
                    obj[k] = int(v)
                elif pd.isna(v):
                    obj[k] = None
                else:
                    obj[k] = v
            recs.append(obj)
        return recs

    # Overall
    overall_path = os.path.join(data_dir, 'overall.json')
    overall_rec = df_to_records(overall)[0] if len(overall) else {}
    with open(overall_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(overall_rec, f, ensure_ascii=False, indent=2)

    # Stocks summary
    stocks_path = os.path.join(data_dir, 'stocks.json')
    stocks_list = df_to_records(stock_summary)
    with open(stocks_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(stocks_list, f, ensure_ascii=False, indent=2)

    # All trades
    trades_path = os.path.join(data_dir, 'trades.json')
    trades_list = df_to_records(trades)
    with open(trades_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(trades_list, f, ensure_ascii=False, indent=2)

    # Monthly metrics
    t = trades.copy()
    if 'sell_date' in t.columns:
        t['month'] = t['sell_date'].dt.strftime('%Y-%m')
    else:
        t['month'] = t['sell_dt'].dt.strftime('%Y-%m')
    months = []
    for month, g in t.groupby('month'):
        total = float(g['pnl'].sum())
        stocks = []
        for code, sg in g.groupby('code'):
            stocks.append({
                'code': str(code),
                'name': sg['name'].iloc[0],
                'pnl': float(sg['pnl'].sum()),
                'trade_count': int(len(sg))
            })
        months.append({'month': month, 'total_pnl': total, 'stocks': stocks})
    months = sorted(months, key=lambda x: x['month'])
    monthly_path = os.path.join(data_dir, 'monthly.json')
    with open(monthly_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(months, f, ensure_ascii=False, indent=2)

    # Per-stock detail: trades + raw records
    raw = trades_raw.copy()
    for code, g in trades.groupby('code'):
        code_str = str(code)
        summ_row = stock_summary[stock_summary['code'] == code].iloc[0].to_dict()
        # trades for this stock
        g_sorted = g.sort_values('sell_dt')
        trades_recs = df_to_records(g_sorted)
        # raw ledger for this stock
        rg = raw[raw['code'].astype(str) == code_str].copy()
        if 'dt' in rg.columns:
            rg = rg.sort_values('dt')
        raw_recs = df_to_records(rg[['date', 'time', 'side', 'qty', 'price', 'fee_total', 'amount', 'net_amount', 'remark']])
        payload = {
            'code': code_str,
            'name': g['name'].iloc[0],
            'summary': {
                'trade_count': int(summ_row.get('trade_count', len(g_sorted))),
                'total_pnl': float(summ_row.get('total_pnl', float(g_sorted['pnl'].sum()))),
                'win_rate_%': float(summ_row.get('win_rate_%', float((g_sorted['pnl'] > 0).mean() * 100.0))),
                'max_win': float(summ_row.get('max_win', float(g_sorted['pnl'].max()))),
                'max_loss': float(summ_row.get('max_loss', float(g_sorted['pnl'].min()))),
                'max_drawdown_%': float(summ_row.get('max_drawdown_%', 0.0)),
                'avg_hold_days': float(summ_row.get('avg_hold_days', float(g_sorted['hold_days'].mean())) if pd.notna(g_sorted['hold_days'].mean()) else 0.0),
                'avg_ret_%': float(summ_row.get('avg_ret_%', float(g_sorted['ret_pct'].dropna().mean() * 100.0)) if len(g_sorted.dropna(subset=['ret_pct'])) else 0.0),
            },
            'trades': trades_recs,
            'raw_records': raw_recs,
        }
        with open(os.path.join(stock_dir, f'{code_str}.json'), 'w', encoding='utf-8') as f:
            import json
            json.dump(payload, f, ensure_ascii=False, indent=2)

def run_once(input_path: str, output_path: str):
    trades_raw = load_trade_excel(input_path)
    trades = fifo_match_and_pnl(trades_raw)
    stock_summary, overall = summarize(trades)
    generate_report_html(trades, stock_summary, overall, output_path)
    # 额外导出JSON供前端使用
    export_json_assets(trades_raw, trades, stock_summary, overall, os.path.join(os.path.dirname(output_path), 'data'))


def main():
    parser = argparse.ArgumentParser(description='生成交易复盘表（HTML）')
    parser.add_argument('--input', '-i', required=True, help='成交报告单xlsx路径')
    parser.add_argument('--output', '-o', default=None, help='输出HTML路径，默认reports/trade_review.html')
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        # 默认输出到当前模块下的 reports/trade_review.html
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports', 'trade_review.html')

    run_once(input_path, output_path)
    print(f'Report generated: {output_path}')
    print(f'JSON exported under: {os.path.join(os.path.dirname(output_path), "data")}')


if __name__ == '__main__':
    main()