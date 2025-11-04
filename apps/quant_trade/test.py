#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
鼎捷策略：日线多头+MACD金叉+RSI过滤+放量+ATR止损止盈
数据来源：本项目后端API（不使用tushare）

运行方式：
1) 回测
   python q.py --mode backtest --code 300378.SZ --start 20240101 --end 20251031
2) 实时扫盘
   python q.py --mode scan --date 20251104

说明：
- 通过 GET /api/stocks/{symbol}/kline 获取K线数据（open/high/low/close/volume）。
- 支持代码格式："shXXXXXX"、"szXXXXXX"、"bjXXXXXX"，以及 "XXXXXX.SH" / "XXXXXX.SZ" / "XXXXXX.BJ"。
- 若使用 "XXXXXX.SH/SZ"，脚本会自动转换为后端使用的前缀格式。
"""
import os, argparse, requests
import numpy as np
import pandas as pd
try:
    import talib as ta
except Exception:
    ta = None
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 后端API基础URL，可通过环境变量 STOCKVIS_API_BASE 覆盖
# 支持容器常见主机映射：localhost 与 host.docker.internal
API_BASE = os.getenv("STOCKVIS_API_BASE", "http://localhost:8080/api")
API_BASE_CANDIDATES = []
if os.getenv("STOCKVIS_API_BASE"):
    API_BASE_CANDIDATES.append(os.getenv("STOCKVIS_API_BASE"))
API_BASE_CANDIDATES.extend([
    "http://localhost:8080/api",
    "http://host.docker.internal:8080/api",
    "http://localhost:8970/api",
    "http://host.docker.internal:8970/api",
])

# 复用HTTP会话以降低连接开销
HTTP_SESSION = requests.Session()

# ---------- 工具 ----------
def _normalize_symbol(code: str) -> str:
    """将常见代码格式转换为后端daily_stock使用的前缀格式。

    例如：
    - "300378.SZ" -> "sz300378"
    - "600089.SH" -> "sh600089"
    - "688981.SH" -> "sh688981"
    - 已是 "sh600000"/"sz300378"/"bj430047" 则原样返回
    - 纯6位数字则原样返回（后端可能支持，但推荐明确前缀）
    """
    if not code:
        return code
    code = code.strip()
    lower = code.lower()
    # 已带前缀
    if lower.startswith(("sh", "sz", "bj")):
        return lower
    # 带 .SH/.SZ/.BJ 后缀
    if "." in code:
        parts = code.split(".")
        if len(parts) == 2 and parts[0].isdigit():
            num, suffix = parts[0], parts[1].upper()
            if suffix == "SH":
                return f"sh{num}"
            if suffix == "SZ":
                return f"sz{num}"
            if suffix == "BJ":
                return f"bj{num}"
    # 其他情况（例如纯数字），直接返回（可能需要后端进行格式映射）
    return code

def get_daily(code: str, start: str, end: str) -> pd.DataFrame:
    """使用本项目后端API获取日线数据（带容器连接回退与健壮解析）。

    参数：
    - code: 股票代码（支持 300378.SZ / 600089.SH / sh600089 / sz300378 等）
    - start: 开始日期（YYYYMMDD）
    - end: 结束日期（YYYYMMDD）

    返回：
    - DataFrame，索引为日期(datetime64)，列：open/high/low/close/volume
    """
    symbol = _normalize_symbol(code)
    start_date = datetime.strptime(start, "%Y%m%d").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y%m%d").strftime("%Y-%m-%d")

    last_error = None
    for base in API_BASE_CANDIDATES:
        url = f"{base}/stocks/{symbol}/kline"
        try:
            resp = HTTP_SESSION.get(url, params={"start_date": start_date, "end_date": end_date}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # 兼容响应两种可能结构：{"symbol":..., "data": [...]} 或直接列表
            records = data.get("data") if isinstance(data, dict) else data
            if not records:
                raise RuntimeError(f"无K线数据: {symbol} {start_date}~{end_date}")

            df = pd.DataFrame(records)
            if "date" not in df.columns:
                raise RuntimeError("响应缺少日期字段 'date'")
            # 只保留所需列，容错缺失列
            for col in ["open", "high", "low", "close", "volume"]:
                if col not in df.columns:
                    df[col] = np.nan
            # 统一类型为数值，无法解析的置为 NaN
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df["trade_date"] = pd.to_datetime(df["date"])  # 与原逻辑统一索引名
            df = df.sort_values("trade_date")
            df.set_index("trade_date", inplace=True)
            return df[["open", "high", "low", "close", "volume"]]
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"获取K线失败（已尝试 {len(API_BASE_CANDIDATES)} 个地址）: {last_error}")

def add_indicators(df):
    """计算所需指标"""
    if ta is None:
        raise RuntimeError("TA-Lib 未安装，无法计算技术指标。请安装 TA-Lib 或在测试中提供替代实现。")
    close = df["close"].values
    high, low = df["high"].values, df["low"].values
    volume = df["volume"].values.astype(float)

    df["ma20"] = ta.SMA(close, 20)
    df["ma60"] = ta.SMA(close, 60)
    df["ma120"] = ta.SMA(close, 120)
    df["rsi14"] = ta.RSI(close, 14)
    df["macd"], df["macdsignal"], df["macdhist"] = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    df["atr14"] = ta.ATR(high, low, close, 14)
    df["vol120"] = ta.SMA(volume, 120)
    return df

def generate_signal(df):
    """按5大条件生成信号"""
    cond1 = (df["close"] > df["ma20"]) & (df["ma20"] > df["ma60"]) & (df["ma60"] > df["ma120"])
    cond2 = (df["macd"] > df["macdsignal"]) & (df["macdhist"] > 0) & (df["macdhist"] > df["macdhist"].shift(1))
    cond3 = (df["rsi14"] > 50) & (df["rsi14"] < 70)
    cond4 = df["volume"] > df["vol120"] * 1.2
    df["signal"] = cond1 & cond2 & cond3 & cond4
    return df

# ---------- 回测 ----------
def backtest(code, start, end, init_cash=1e6, pos_ratio=0.2):
    df = add_indicators(get_daily(code, start, end))
    df = generate_signal(df)
    cash, pos, entry_price = init_cash, 0, 0
    df["nav"] = np.nan
    stop_loss, take_profit = np.nan, np.nan

    for i, (dt, row) in enumerate(df.iterrows()):
        # 更新止损/止盈
        if pos > 0:
            stop_loss  = entry_price - 1.5 * row["atr14"]
            take_profit = entry_price + 3.0 * row["atr14"]   # 1:2 风险回报
            if row["low"] <= stop_loss:
                cash = pos * stop_loss
                pos = 0
            elif row["high"] >= take_profit:
                cash = pos * take_profit
                pos = 0

        # 开仓
        if pos == 0 and row["signal"]:
            pos = init_cash * pos_ratio / row["close"]
            entry_price = row["close"]
            cash -= init_cash * pos_ratio

        df.loc[dt, "nav"] = cash + (pos * row["close"] if pos else 0)

    df["nav"] /= init_cash
    print("回测总收益：%.2f %%" % ((df["nav"].iloc[-1] - 1) * 100))
    df[["close", "nav"]].plot(figsize=(12, 5), secondary_y="nav", title=code)
    plt.show()
    return df

# ---------- 实时扫描 ----------
def scan(date):
    """扫全市场（或自选池）"""
    # 代码示例，可按需替换为你的自选池
    codes = [
        "300378.SZ", "300073.SZ", "002629.SZ", "600089.SH",
        "600121.SH", "000426.SZ", "603993.SH", "600489.SH",
        "002460.SZ", "000776.SZ", "518880.SH", "002594.SZ",
        "204001.SH", "513010.SH"
    ]
    date_str = date.strftime("%Y%m%d")
    res = []
    for code in codes:
        try:
            start = (date - timedelta(200)).strftime("%Y%m%d")
            df = add_indicators(get_daily(code, start, date_str))
            df = generate_signal(df)
            latest = df.iloc[-1]
            if latest["signal"]:
                res.append({"code": code, "close": round(latest["close"], 2),
                            "rsi": round(latest["rsi14"], 2),
                            "atr": round(latest["atr14"], 2)})
        except Exception as e:
            print(f"扫描 {code} 失败: {e}")
            continue
    print("【%s 扫描结果】触发买入信号：" % date.strftime("%Y-%m-%d"))
    print(pd.DataFrame(res))

# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["backtest", "scan"], required=True)
    parser.add_argument("--code", help="个股代码，如 300378.SZ")
    parser.add_argument("--start", help="回测开始 20240101")
    parser.add_argument("--end", help="回测结束 20251031")
    parser.add_argument("--date", help="扫描日期 20251104")
    args = parser.parse_args()

    if args.mode == "backtest":
        backtest(args.code, args.start, args.end)
    else:
        d = datetime.strptime(args.date, "%Y%m%d") if args.date else datetime.today()
        scan(d)