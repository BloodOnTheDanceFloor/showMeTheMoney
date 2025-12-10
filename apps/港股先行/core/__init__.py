"""
港股先行指标监控程序 - 核心模块包
"""

from .monitor import start_monitoring, is_trading_time
from .data_fetcher import get_realtime_data, get_historical_data, get_early_rise
from .alarm import show_condition1_alarm, show_condition2_alarm, show_condition3_alarm
from .backtest import backtest_all_conditions, print_win_rate_table, backtest_condition1, backtest_condition2, backtest_condition3

__version__ = "1.0.0"
__all__ = [
    "start_monitoring", "is_trading_time",
    "get_realtime_data", "get_historical_data", "get_early_rise",
    "show_condition1_alarm", "show_condition2_alarm", "show_condition3_alarm",
    "backtest_all_conditions", "print_win_rate_table", "backtest_condition1", "backtest_condition2", "backtest_condition3"
]