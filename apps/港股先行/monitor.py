#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控模块
"""

import time
from datetime import datetime
from data_fetcher import get_realtime_data, get_early_rise
from alarm import show_condition1_alarm, show_condition2_alarm, show_condition3_alarm
from config import DEFAULT_CONFIG
from logger import setup_logger

# 设置日志
logger = setup_logger()

def is_trading_time():
    """
    判断当前是否在交易时间内
    
    返回:
        bool: True表示在交易时间内
    """
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    # 解析交易时间
    start_time = datetime.strptime(f"{today} {DEFAULT_CONFIG['trading_start_time']}", '%Y-%m-%d %H:%M')
    end_time = datetime.strptime(f"{today} {DEFAULT_CONFIG['trading_end_time']}", '%Y-%m-%d %H:%M')
    
    # 判断是否在交易时间内
    return start_time <= now <= end_time

def check_condition1(hsi_data, csi300_data, window_min, hsi_rise_thresh, csi300_rise_thresh):
    """
    检查条件1: 恒指窗口涨幅 >1.5% 且沪深300窗口涨幅 <0.5%
    
    参数:
        hsi_data: 恒指数据
        csi300_data: 沪深300数据
        window_min: 窗口分钟数
        hsi_rise_thresh: 恒指涨幅阈值
        csi300_rise_thresh: 沪深300涨幅阈值
    
    返回:
        bool: 是否触发条件
    """
    # 计算窗口涨幅
    hsi_rise = get_early_rise(hsi_data, window_min)
    csi300_rise = get_early_rise(csi300_data, window_min)
    
    # 条件判断
    is_triggered = hsi_rise > hsi_rise_thresh and csi300_rise < csi300_rise_thresh
    
    logger.info(f"条件1检查: 恒指涨幅={hsi_rise:.2f}%, 沪深300涨幅={csi300_rise:.2f}% -> {'触发' if is_triggered else '未触发'}")
    
    return is_triggered

def check_condition2(hsi_data, hs_tech_data, window_min, hsi_rise_thresh, hs_tech_rise_thresh):
    """
    检查条件2: 恒指或恒生科技窗口涨幅 >1%
    
    参数:
        hsi_data: 恒指数据
        hs_tech_data: 恒生科技数据
        window_min: 窗口分钟数
        hsi_rise_thresh: 恒指涨幅阈值
        hs_tech_rise_thresh: 恒生科技涨幅阈值
    
    返回:
        bool: 是否触发条件
    """
    # 计算窗口涨幅
    hsi_rise = get_early_rise(hsi_data, window_min)
    hs_tech_rise = get_early_rise(hs_tech_data, window_min)
    
    # 条件判断
    is_triggered = hsi_rise > hsi_rise_thresh or hs_tech_rise > hs_tech_rise_thresh
    
    logger.info(f"条件2检查: 恒指涨幅={hsi_rise:.2f}%, 恒生科技涨幅={hs_tech_rise:.2f}% -> {'触发' if is_triggered else '未触发'}")
    
    return is_triggered

def check_condition3(hsi_data, csi300_data, ic_data, window_min, hsi_rise_thresh, basis_converge_thresh):
    """
    检查条件3: 恒指窗口涨幅 >1.5% 且沪深300期指贴水在窗口内收敛 >0.5%
    
    参数:
        hsi_data: 恒指数据
        csi300_data: 沪深300现货数据
        ic_data: 沪深300期货数据
        window_min: 窗口分钟数
        hsi_rise_thresh: 恒指涨幅阈值
        basis_converge_thresh: 基差收敛阈值
    
    返回:
        bool: 是否触发条件
    """
    # 计算恒指窗口涨幅
    hsi_rise = get_early_rise(hsi_data, window_min)
    
    # 计算基差收敛
    if not csi300_data.empty and not ic_data.empty:
        # 获取窗口内的现货和期货数据
        today = datetime.now().date()
        csi300_today = csi300_data[csi300_data['datetime'].dt.date == today]
        ic_today = ic_data[ic_data['datetime'].dt.date == today]
        
        if not csi300_today.empty and not ic_today.empty:
            # 获取窗口开始和结束的基差
            window_start = csi300_today.iloc[0]['datetime'].time()
            window_end = (datetime.combine(datetime.today(), window_start) + 
                         time.timedelta(minutes=window_min)).time()
            
            # 窗口开始时的基差
            start_csi300 = csi300_today.iloc[0]['close']
            start_ic = ic_today.iloc[0]['close']
            start_basis = (start_ic - start_csi300) / start_csi300 * 100
            
            # 窗口结束时的基差
            end_csi300 = csi300_today.iloc[-1]['close']
            end_ic = ic_today.iloc[-1]['close']
            end_basis = (end_ic - end_csi300) / end_csi300 * 100
            
            # 基差收敛幅度
            basis_converge = end_basis - start_basis  # 正表示收敛
            
            # 条件判断
            is_triggered = hsi_rise > hsi_rise_thresh and basis_converge > basis_converge_thresh
            
            logger.info(f"条件3检查: 恒指涨幅={hsi_rise:.2f}%, 基差收敛={basis_converge:.2f}% -> {'触发' if is_triggered else '未触发'}")
            
            return is_triggered
    
    logger.info(f"条件3检查: 数据不足 -> 未触发")
    return False

def start_monitoring(config, win_rates):
    """
    开始监控
    
    参数:
        config: 配置字典
        win_rates: 各条件胜率
    """
    logger.info("开始监控A股国家队托市信号")
    
    # 触发标志位（每日重置）
    triggered_flags = {
        'condition1': False,
        'condition2': False,
        'condition3': False
    }
    
    # 上次重置日期
    last_reset_date = datetime.now().date()
    
    try:
        while True:
            # 获取当前时间
            now = datetime.now()
            current_date = now.date()
            
            # 每日重置触发标志位
            if current_date != last_reset_date:
                triggered_flags = {
                    'condition1': False,
                    'condition2': False,
                    'condition3': False
                }
                last_reset_date = current_date
                logger.info("每日重置触发标志位")
            
            # 判断是否在交易时间内
            if is_trading_time():
                logger.info("开始检查条件...")
                
                # 获取实时数据
                period = config['period']
                
                # 获取恒指数据
                hsi_data = get_realtime_data('hk', 'HSI', period)
                
                # 获取恒生科技数据
                hs_tech_data = get_realtime_data('hk', 'HSTECH', period)
                
                # 获取沪深300现货数据
                csi300_data = get_realtime_data('a_index', '000300', period)
                
                # 获取沪深300期货数据
                ic_data = get_realtime_data('futures', 'IC0', period)
                
                # 检查条件1
                if not triggered_flags['condition1']:
                    if check_condition1(hsi_data, csi300_data, config['window_min'], 
                                      config['hsi_rise_thresh'], config['csi300_rise_thresh']):
                        # 触发报警
                        show_condition1_alarm(win_rates['condition1'], config['window_min'],
                                            config['hsi_rise_thresh'], config['csi300_rise_thresh'])
                        triggered_flags['condition1'] = True
                
                # 检查条件2
                if not triggered_flags['condition2']:
                    if check_condition2(hsi_data, hs_tech_data, config['window_min'], 
                                      config['hsi_rise_thresh'], config['hs_tech_rise_thresh']):
                        # 触发报警
                        show_condition2_alarm(win_rates['condition2'], config['window_min'],
                                            config['hsi_rise_thresh'], config['hs_tech_rise_thresh'])
                        triggered_flags['condition2'] = True
                
                # 检查条件3
                if not triggered_flags['condition3']:
                    if check_condition3(hsi_data, csi300_data, ic_data, config['window_min'], 
                                      config['hsi_rise_thresh'], config['basis_converge_thresh']):
                        # 触发报警
                        show_condition3_alarm(win_rates['condition3'], config['window_min'],
                                            config['hsi_rise_thresh'], config['basis_converge_thresh'])
                        triggered_flags['condition3'] = True
            else:
                logger.info(f"当前非交易时间 ({now.strftime('%H:%M:%S')})，跳过检查")
            
            # 等待5分钟后再次检查
            logger.info(f"等待 {DEFAULT_CONFIG['check_interval']} 秒后再次检查...")
            time.sleep(DEFAULT_CONFIG['check_interval'])
            
    except KeyboardInterrupt:
        logger.info("监控被用户中断")
    except Exception as e:
        logger.error(f"监控异常: {str(e)}")
        raise
