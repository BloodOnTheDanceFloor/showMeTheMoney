#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股国家队托市信号监控程序
"""

import sys
import time
import argparse
from datetime import datetime

# 导入自定义模块 - 重构后的模块结构
from data.config import DEFAULT_CONFIG, SUPPORTED_PERIODS, SYMBOL_MAPPING, SUPPORT_MEASURE_DATES
from core.data_fetcher import get_historical_data, get_realtime_data, get_early_rise
from core.backtest import backtest_all_conditions, print_win_rate_table
from core.monitor import start_monitoring
from utils.logger import setup_logger
from utils import start_proxy_health_check, get_proxy_health_status

# 设置日志
logger = setup_logger()

def main():
    """主函数"""
    # 设置日志
    logger = setup_logger()
    logger.info("A股国家队托市信号监控程序启动")
    
    # 禁用代理健康检查，使用直连模式
    logger.info("使用直连模式，不启用代理健康检查")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='A股国家队托市信号监控程序')
    parser.add_argument('--window-min', type=int, default=DEFAULT_CONFIG['window_min'],
                        help='早盘窗口分钟数 (默认: 30)')
    parser.add_argument('--hsi-rise-thresh', type=float, default=DEFAULT_CONFIG['hsi_rise_thresh'],
                        help='恒指涨幅阈值百分比 (默认: 1.5)')
    parser.add_argument('--hs-tech-rise-thresh', type=float, default=DEFAULT_CONFIG['hs_tech_rise_thresh'],
                        help='恒生科技涨幅阈值百分比 (默认: 1.0)')
    parser.add_argument('--csi300-rise-thresh', type=float, default=DEFAULT_CONFIG['csi300_rise_thresh'],
                        help='沪深300涨幅阈值百分比 (默认: 0.5)')
    parser.add_argument('--basis-converge-thresh', type=float, default=DEFAULT_CONFIG['basis_converge_thresh'],
                        help='基差收敛阈值百分比 (默认: 0.5)')
    parser.add_argument('--period', type=str, default=DEFAULT_CONFIG['period'],
                        choices=SUPPORTED_PERIODS, help='数据周期 (默认: 1)')
    parser.add_argument('--test-only', action='store_true',
                        help='仅运行回测，不进入监控模式')
    parser.add_argument('--no-monitor', action='store_true',
                        help='跳过实时监控')
    
    args = parser.parse_args()
    
    # 合并配置
    config = {
        'window_min': args.window_min,
        'hsi_rise_thresh': args.hsi_rise_thresh,
        'hs_tech_rise_thresh': args.hs_tech_rise_thresh,
        'csi300_rise_thresh': args.csi300_rise_thresh,
        'basis_converge_thresh': args.basis_converge_thresh,
        'period': args.period
    }
    
    print("=" * 60)
    print("A股国家队托市信号监控程序")
    print("=" * 60)
    print("免责声明：本程序仅供学习参考，不构成投资建议")
    print(f"当前配置：窗口={config['window_min']}min, 恒指涨幅阈值={config['hsi_rise_thresh']}%, 基差收敛阈值={config['basis_converge_thresh']}%")
    print("=" * 60)
    
    # 显示代理健康状态
    proxy_status = get_proxy_health_status()
    logger.info(f"代理池状态: {proxy_status['healthy_proxies']}/{proxy_status['total_proxies']} 健康 (健康率: {proxy_status['health_rate']:.1f}%)")
    
    try:
        # 1. 运行回测
        logger.info("开始执行回测...")
        print("\n开始回测...")
        win_rates = backtest_all_conditions(config)
        
        # 2. 输出胜率表格
        print_win_rate_table(win_rates, config)
        
        # 3. 进入监控模式（如果不是仅测试）
        if not args.test_only and not args.no_monitor:
            logger.info("开始实时监控...")
            print("\n开始监控...")
            print("按 Ctrl+C 退出监控")
            print("=" * 60)
            start_monitoring(config, win_rates)
        else:
            logger.info("跳过实时监控")
        
    except KeyboardInterrupt:
        logger.info("用户中断监控")
        print("\n程序已退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
        print(f"\n程序异常: {str(e)}")
        sys.exit(1)
    finally:
        # 不需要停止代理健康检查，因为我们没有启用它
        logger.info("程序结束")

if __name__ == "__main__":
    main()
