#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块
"""

import time
import akshare as ak
import pandas as pd
import random
import requests
from datetime import datetime, timedelta
from utils.logger import setup_logger
from utils.proxy_pool import get_proxy_session

# 设置日志
logger = setup_logger()

# 数据缓存机制
data_cache = {}
cache_timeout = 300  # 缓存5分钟

def is_cache_valid(cache_key):
    """检查缓存是否有效"""
    if cache_key in data_cache:
        cache_time, cache_data = data_cache[cache_key]
        if datetime.now() - cache_time < timedelta(seconds=cache_timeout):
            return True
        else:
            del data_cache[cache_key]
    return False

def get_cached_data(cache_key):
    """获取缓存数据"""
    if is_cache_valid(cache_key):
        logger.info(f"使用缓存数据: {cache_key}")
        return data_cache[cache_key][1]
    return None

def set_cache_data(cache_key, data):
    """设置缓存数据"""
    data_cache[cache_key] = (datetime.now(), data)
    logger.info(f"设置缓存数据: {cache_key}")

def add_random_delay():
    """添加随机延迟，避免固定频率请求"""
    delay = random.uniform(3, 8)  # 3-8秒随机延迟，增加等待时间
    logger.info(f"添加随机延迟: {delay:.2f}秒")
    time.sleep(delay)



# API重试配置
MAX_RETRIES = 5  # 增加到5次重试
RETRY_DELAY = 15  # 延长到15秒，避免频繁重试

def retry_on_failure(func):
    """API调用失败重试装饰器（优化版）"""
    def wrapper(*args, **kwargs):
        for i in range(MAX_RETRIES):
            try:
                # 添加随机延迟
                if i > 0:  # 第一次不延迟
                    add_random_delay()
                return func(*args, **kwargs)
            except Exception as e:
                if i == MAX_RETRIES - 1:
                    logger.error(f"API调用失败，已达最大重试次数: {str(e)}")
                    raise
                # 递增重试延迟
                retry_delay = RETRY_DELAY * (i + 1) + random.uniform(1, 3)
                logger.warning(f"API调用失败，{retry_delay:.1f}秒后重试 ({i+1}/{MAX_RETRIES}): {str(e)}")
                time.sleep(retry_delay)
    return wrapper

@retry_on_failure
def get_hk_stock_data(symbol, period):
    """获取港股指数数据"""
    logger.info(f"获取港股指数数据: {symbol}, 周期: {period}")
    
    # 生成缓存键
    cache_key = f"hk_{symbol}_{period}"
    
    # 检查缓存
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        return cached_data
    
    # 港股指数代码映射
    index_map = {
        'HSI': '恒生指数',
        'HSTECH': '恒生科技指数'
    }
    
    if symbol in index_map:
        # 获取港股指数数据 - 使用直连，不使用代理
        logger.info("使用直连获取港股指数数据，不使用代理")
        # 显式禁用代理
        import os
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        # 禁用 requests 代理
        data = ak.stock_hk_index_daily_em(symbol=symbol, proxies={"http": None, "https": None})
    else:
        # 获取港股个股数据 - 使用直连，不使用代理
        logger.info("使用直连获取港股个股数据，不使用代理")
        # 显式禁用代理
        import os
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        # 禁用 requests 代理
        data = ak.stock_hk_hist(symbol=symbol, period=period, proxies={"http": None, "https": None})
    
    # 设置缓存
    set_cache_data(cache_key, data)
    return data

@retry_on_failure
def get_a_index_data(symbol, period):
    """获取A股指数数据"""
    logger.info(f"获取A股指数数据: {symbol}, 周期: {period}")
    
    # 生成缓存键
    cache_key = f"a_index_{symbol}_{period}"
    
    # 检查缓存
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        return cached_data
    
    # A股指数代码映射
    index_map = {
        '000300': '沪深300',
        'sh000300': '沪深300',
        'sz399300': '沪深300'
    }
    
    # 使用正确的A股指数接口 - 使用直连，不使用代理
    logger.info("使用直连获取A股指数数据，不使用代理")
    # 禁用 requests 代理
    data = ak.index_zh_a_hist(symbol=symbol, period=period, proxies={"http": None, "https": None})
    
    # 设置缓存
    set_cache_data(cache_key, data)
    return data

@retry_on_failure
def get_futures_data(symbol, period):
    """获取期货分钟数据"""
    logger.info(f"获取期货数据: {symbol}, 周期: {period}")
    
    # 生成缓存键
    cache_key = f"futures_{symbol}_{period}"
    
    # 检查缓存
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        return cached_data
    
    # 获取期货数据 - 使用直连，不使用代理
    logger.info("使用直连获取期货数据，不使用代理")
    # 禁用 requests 代理
    data = ak.futures_zh_minute_sina(symbol=symbol, period=period, proxies={"http": None, "https": None})
    
    # 设置缓存
    set_cache_data(cache_key, data)
    return data

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
