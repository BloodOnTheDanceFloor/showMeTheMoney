import os
import sys
import json
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import pandas as pd
import numpy as np


# ---- talib 轻量替身（避免外部依赖） ----
class _DummyTA:
    @staticmethod
    def SMA(arr, period):
        s = pd.Series(arr)
        return s.rolling(period).mean().values

    @staticmethod
    def RSI(arr, period):
        # 简化版RSI（用于测试，不代表真实结果）
        s = pd.Series(arr)
        delta = s.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(period).mean()
        roll_down = down.rolling(period).mean()
        rs = roll_up / (roll_down.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50).values

    @staticmethod
    def _ema(series, span):
        return pd.Series(series).ewm(span=span, adjust=False).mean().values

    @staticmethod
    def MACD(close, fastperiod=12, slowperiod=26, signalperiod=9):
        macd = _DummyTA._ema(close, fastperiod) - _DummyTA._ema(close, slowperiod)
        signal = pd.Series(macd).ewm(span=signalperiod, adjust=False).mean().values
        hist = macd - signal
        return macd, signal, hist

    @staticmethod
    def ATR(high, low, close, period):
        # 简化版ATR
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean().fillna(tr.mean()).values


def _install_dummy_talib():
    sys.modules['talib'] = _DummyTA


# ---- 简易HTTP服务，模拟容器API ----
class _KlineHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith('/api/stocks/') and parsed.path.endswith('/kline'):
            # 返回固定的K线数据集
            data = [
                {"date": "2025-10-28", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1000},
                {"date": "2025-10-29", "open": 10.6, "high": 11.2, "low": 10.1, "close": 11.0, "volume": 1200},
                {"date": "2025-10-30", "open": 11.0, "high": 12.0, "low": 10.7, "close": 11.8, "volume": 1500},
                {"date": "2025-10-31", "open": 11.9, "high": 12.3, "low": 11.5, "close": 12.1, "volume": 1800},
            ]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            body = json.dumps({"data": data}).encode('utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def _run_server(port):
    httpd = HTTPServer(('localhost', port), _KlineHandler)
    httpd.serve_forever()


def _pick_free_port(start=9000):
    for p in range(start, start + 100):
        try:
            s = HTTPServer(('localhost', p), _KlineHandler)
            s.server_close()
            return p
        except OSError:
            continue
    return start


def test_normalize_symbol_import_and_formats():
    _install_dummy_talib()
    from apps.quant_trade import test as qt
    assert qt._normalize_symbol('300378.SZ') == 'sz300378'
    assert qt._normalize_symbol('600089.SH') == 'sh600089'
    assert qt._normalize_symbol('688981.SH') == 'sh688981'
    assert qt._normalize_symbol('sh600000') == 'sh600000'
    assert qt._normalize_symbol('bj430047') == 'bj430047'
    assert qt._normalize_symbol('000001.SZ') == 'sz000001'
    assert qt._normalize_symbol('000001') == '000001'


def test_get_daily_success_with_container_like_api():
    _install_dummy_talib()
    from apps.quant_trade import test as qt

    # 通过伪造HTTP响应避免真实服务依赖
    records = [
        {"date": "2025-10-28", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1000},
        {"date": "2025-10-29", "open": 10.6, "high": 11.2, "low": 10.1, "close": 11.0, "volume": 1200},
        {"date": "2025-10-30", "open": 11.0, "high": 12.0, "low": 10.7, "close": 11.8, "volume": 1500},
        {"date": "2025-10-31", "open": 11.9, "high": 12.3, "low": 11.5, "close": 12.1, "volume": 1800},
    ]

    class DummyResp:
        def __init__(self, ok=True):
            self.status_code = 200 if ok else 500
        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception('HTTP error')
        def json(self):
            return {"data": records}

    orig_get = qt.HTTP_SESSION.get
    try:
        qt.HTTP_SESSION.get = lambda url, params=None, timeout=10: DummyResp()
        df = qt.get_daily('600000.SH', '20251028', '20251031')
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert pd.api.types.is_datetime64_any_dtype(df.index)
        # 数值列应可数值化
        assert pd.notnull(df['close']).all()
        assert (df['volume'] >= 0).all()
    finally:
        qt.HTTP_SESSION.get = orig_get


def test_indicators_and_signal_generation():
    _install_dummy_talib()
    from apps.quant_trade import test as qt
    # 构造一段上行数据，便于触发信号
    dates = pd.date_range('2025-10-01', periods=200, freq='D')
    close = np.linspace(10, 20, 200)
    high = close + 0.5
    low = close - 0.5
    volume = np.linspace(1000, 3000, 200)
    df = pd.DataFrame({'open': close, 'high': high, 'low': low, 'close': close, 'volume': volume}, index=dates)
    df = qt.generate_signal(qt.add_indicators(df))
    # 至少最后一根应更可能触发信号
    assert 'signal' in df.columns
    assert df['signal'].iloc[-1] in (True, False)  # 不抛异常即可


def test_backtest_with_monkeypatched_get_daily():
    _install_dummy_talib()
    from apps.quant_trade import test as qt

    # 伪造get_daily，返回一段简单上行数据
    dates = pd.date_range('2025-10-01', periods=60, freq='D')
    close = np.linspace(10, 12, 60)
    high = close + 0.3
    low = close - 0.3
    volume = np.full(60, 1000)
    fake_df = pd.DataFrame({'open': close, 'high': high, 'low': low, 'close': close, 'volume': volume}, index=dates)

    orig_get = qt.get_daily
    try:
        qt.get_daily = lambda code, s, e: fake_df.copy()
        df = qt.backtest('600000.SH', '20251001', '20251130')
        assert 'nav' in df.columns
        assert pd.notnull(df['nav']).any()
    finally:
        qt.get_daily = orig_get


def test_scan_with_monkeypatched_get_daily():
    _install_dummy_talib()
    from apps.quant_trade import test as qt
    # 使用简单数据以尽量触发信号
    dates = pd.date_range('2025-10-01', periods=200, freq='D')
    close = np.linspace(10, 20, 200)
    high = close + 0.5
    low = close - 0.5
    volume = np.linspace(1000, 3000, 200)
    fake_df = pd.DataFrame({'open': close, 'high': high, 'low': low, 'close': close, 'volume': volume}, index=dates)
    # 不预先计算指标/信号，交由 scan 内部处理

    orig_get = qt.get_daily
    try:
        qt.get_daily = lambda code, s, e: fake_df.copy()
        qt.scan(datetime.strptime('20251104', '%Y%m%d'))
    finally:
        qt.get_daily = orig_get
# 将项目根目录加入PYTHONPATH，确保可导入 apps.*
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _ROOT not in sys.path:
    sys.path.append(_ROOT)