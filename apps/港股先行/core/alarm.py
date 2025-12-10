#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警模块
"""

import tkinter as tk
from tkinter import messagebox
from utils.logger import setup_logger

# 设置日志
logger = setup_logger()

# 确保只创建一个Tk实例
root = None

def init_tk():
    """初始化Tk实例"""
    global root
    if root is None:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

def show_alarm(condition_num, description, suggestion, win_rate, window_min, thresholds):
    """
    弹出报警窗口
    
    参数:
        condition_num: 条件编号
        description: 条件描述
        suggestion: 建议
        win_rate: 历史胜率
        window_min: 窗口分钟数
        thresholds: 阈值描述
    """
    # 初始化Tk
    init_tk()
    
    # 格式化报警信息
    message = f"条件{condition_num}触发：{description}！可能国家队出手，{suggestion}。（历史胜率：{win_rate:.1f}%，基于{window_min}min窗口、{thresholds}阈值回测）"
    
    # 弹出弹窗
    messagebox.showinfo(title="A股国家队托市信号", message=message)
    
    # 记录日志
    logger.info(f"报警触发: {message}")

def show_condition1_alarm(win_rate, window_min, hsi_thresh, csi300_thresh):
    """显示条件1报警"""
    description = "港股先涨为敬"
    suggestion = "A股或跟进"
    thresholds = f">{hsi_thresh}%恒指涨幅、<{csi300_thresh}%沪深300涨幅"
    show_alarm(1, description, suggestion, win_rate, window_min, thresholds)

def show_condition2_alarm(win_rate, window_min, hsi_thresh, hs_tech_thresh):
    """显示条件2报警"""
    description = "早盘强度高"
    suggestion = "国家队拉升概率提升"
    thresholds = f">{hsi_thresh}%恒指或>{hs_tech_thresh}%恒生科技涨幅"
    show_alarm(2, description, suggestion, win_rate, window_min, thresholds)

def show_condition3_alarm(win_rate, window_min, hsi_thresh, basis_thresh):
    """显示条件3报警"""
    description = "组合信号"
    suggestion = "捕捉托市行情"
    thresholds = f">{hsi_thresh}%恒指涨幅、>{basis_thresh}%基差收敛"
    show_alarm(3, description, suggestion, win_rate, window_min, thresholds)
