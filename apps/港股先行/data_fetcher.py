#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块
"""

import time
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from logger import setup_logger

# 设置日志
logger = setup_logger()

# API重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒

def retry_on_failure(func):
    """API调用失败重试装饰器"""
    def wrapper(*args, **kwargs):
        for i in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == MAX_RETRIES - 1:
                    logger.error(f"API调用失败，已达最大重试次数: {str(e)}")
                    raise
                logger.warning(f"API调用失败，{RETRY_DELAY}秒后重试 ({i+1}/{MAX_RETRIES}): {str(e)}")
                time.sleep(RETRY_DELAY)
    return wrapper

@retry_on_failure
def get_hk_stock_data(symbol, period):
    """获取港股分钟数据"""
    logger.info(f"获取港股数据: {symbol}, 周期: {period}")
    return ak.stock_hk_hist_min_em(symbol=symbol, period=period)

@retry_on_failure
def get_a_index_data(symbol, period):
    """获取A股指数分钟数据"""
    logger.info(f"获取A股指数数据: {symbol}, 周期: {period}")
    return ak.index_zh_a_hist_min_em(symbol=symbol, period=period)

@retry_on_failure
def get_futures_data(symbol, period):
    """获取期货分钟数据"""
    logger.info(f"获取期货数据: {symbol}, 周期: {period}")
    return ak.futures_zh_minute_sina(symbol=symbol, period=period)

def get_historical_data(symbol_type, symbol, start_date, end_date, period):
    """
    获取历史分钟数据
    
    参数:
        symbol_type: 数据类型 ('hk'/'a_index'/'futures')
        symbol: 代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        period: 周期
    
    返回:
        pandas.DataFrame: 历史数据
    """
    logger.info(f"获取历史数据: {symbol_type}, {symbol}, {start_date} 到 {end_date}")
    
    # 由于AKShare的历史分钟数据API可能有日期限制，这里简化处理
    # 实际使用时可能需要按日期循环获取
    try:
        if symbol_type == 'hk':
            data = get_hk_stock_data(symbol, period)
        elif symbol_type == 'a_index':
            data = get_a_index_data(symbol, period)
        elif symbol_type == 'futures':
            data = get_futures_data(symbol, period)
        else:
            raise ValueError(f"不支持的数据类型: {symbol_type}")
        
        # 转换时间列
        if '日期' in data.columns:
            data['datetime'] = pd.to_datetime(data['日期'])
        elif 'datetime' not in data.columns:
            # 尝试自动识别时间列
            for col in data.columns:
                if 'time' in col.lower() or '日期' in col or '时间' in col:
                    data['datetime'] = pd.to_datetime(data[col])
                    break
        
        # 过滤日期范围
        data = data[(data['datetime'] >= start_date) & (data['datetime'] <= end_date)]
        
        return data
    except Exception as e:
        logger.error(f"获取历史数据失败: {str(e)}")
        return pd.DataFrame()

def get_realtime_data(symbol_type, symbol, period):
    """
    获取实时分钟数据
    
    参数:
        symbol_type: 数据类型 ('hk'/'a_index'/'futures')
        symbol: 代码
        period: 周期
    
    返回:
        pandas.DataFrame: 实时数据
    """
    logger.info(f"获取实时数据: {symbol_type}, {symbol}, 周期: {period}")
    
    try:
        if symbol_type == 'hk':
            data = get_hk_stock_data(symbol, period)
        elif symbol_type == 'a_index':
            data = get_a_index_data(symbol, period)
        elif symbol_type == 'futures':
            data = get_futures_data(symbol, period)
        else:
            raise ValueError(f"不支持的数据类型: {symbol_type}")
        
        # 转换时间列
        if '日期' in data.columns:
            data['datetime'] = pd.to_datetime(data['日期'])
        elif 'datetime' not in data.columns:
            # 尝试自动识别时间列
            for col in data.columns:
                if 'time' in col.lower() or '日期' in col or '时间' in col:
                    data['datetime'] = pd.to_datetime(data[col])
                    break
        
        return data
    except Exception as e:
        logger.error(f"获取实时数据失败: {str(e)}")
        return pd.DataFrame()

def get_early_rise(data, window_min, start_time_str='09:30'):
    """
    计算窗口涨幅
    
    参数:
        data: DataFrame，包含datetime和close列
        window_min: 窗口分钟数
        start_time_str: 开盘时间字符串
    
    返回:
        float: 涨幅百分比
    """
    if data.empty:
        return 0.0
    
    # 转换开盘时间
    start_time = pd.to_datetime(start_time_str).time()
    
    # 过滤出当天的数据
    today = datetime.now().date()
    data_today = data[data['datetime'].dt.date == today]
    
    if data_today.empty:
        return 0.0
    
    # 过滤出开盘后的数据
    data_after_open = data_today[data_today['datetime'].dt.time >= start_time]
    
    if data_after_open.empty:
        return 0.0
    
    # 获取开盘价
    open_price = data_after_open.iloc[0]['close']
    
    # 计算窗口结束时间
    window_end_time = (datetime.combine(datetime.today(), start_time) + 
                      timedelta(minutes=window_min)).time()
    
    # 过滤出窗口内的数据
    data_window = data_after_open[data_after_open['datetime'].dt.time <= window_end_time]
    
    if data_window.empty:
        return 0.0
    
    # 获取窗口结束价格
    window_end_price = data_window.iloc[-1]['close']
    
    # 计算涨幅百分比
    rise_pct = (window_end_price - open_price) / open_price * 100
    
    return round(rise_pct, 2)
