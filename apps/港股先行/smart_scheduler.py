#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能调度器 - 在每个交易日9:15-10:30自动运行监控程序
"""

import time
import subprocess
import signal
import sys
from datetime import datetime, timedelta
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingScheduler:
    def __init__(self):
        self.process = None
        self.running = True
        self.start_time = "09:15"
        self.end_time = "10:30"
        self.python_path = sys.executable
        self.script_path = Path(__file__).parent / "main.py"
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        logger.info(f"收到信号 {signum}，准备退出...")
        self.running = False
        self.stop_monitor()
        sys.exit(0)
        
    def is_trading_day(self):
        """判断今天是否为交易日（周一至周五）"""
        today = datetime.now().weekday()
        return 0 <= today <= 4  # 0=周一, 4=周五
        
    def is_trading_time(self):
        """判断当前是否在交易时间内"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        return self.start_time <= current_time <= self.end_time
        
    def should_start_monitor(self):
        """判断是否应该启动监控"""
        if not self.is_trading_day():
            return False
            
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 如果当前时间在交易时间内，应该启动
        if self.is_trading_time():
            return True
            
        return False
        
    def start_monitor(self):
        """启动监控程序"""
        try:
            logger.info("启动监控程序...")
            self.process = subprocess.Popen(
                [self.python_path, str(self.script_path)],
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"监控程序已启动，PID: {self.process.pid}")
            return True
        except Exception as e:
            logger.error(f"启动监控程序失败: {e}")
            return False
            
    def stop_monitor(self):
        """停止监控程序"""
        if self.process and self.process.poll() is None:
            try:
                logger.info("停止监控程序...")
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("监控程序已停止")
            except subprocess.TimeoutExpired:
                logger.warning("监控程序未正常停止，强制结束")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"停止监控程序失败: {e}")
        self.process = None
        
    def check_process_health(self):
        """检查进程健康状态"""
        if self.process is None:
            return False
            
        return_code = self.process.poll()
        if return_code is None:
            return True  # 进程仍在运行
        else:
            logger.warning(f"监控程序异常退出，返回码: {return_code}")
            return False
            
    def run(self):
        """主循环"""
        logger.info("智能调度器启动")
        logger.info(f"交易时间: {self.start_time} - {self.end_time}")
        logger.info(f"Python路径: {self.python_path}")
        logger.info(f"脚本路径: {self.script_path}")
        
        while self.running:
            try:
                now = datetime.now()
                logger.info(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S %A')}")
                
                if self.is_trading_day():
                    logger.info("今天是交易日")
                    
                    if self.should_start_monitor():
                        logger.info("当前在交易时间内")
                        
                        if not self.process or not self.check_process_health():
                            logger.info("监控程序未运行，准备启动...")
                            self.start_monitor()
                        else:
                            logger.info("监控程序运行正常")
                    else:
                        logger.info("当前不在交易时间内")
                        
                        if self.process and self.check_process_health():
                            logger.info("监控程序正在运行，准备停止...")
                            self.stop_monitor()
                        else:
                            logger.info("监控程序未运行")
                            
                    # 计算下次检查时间
                    if self.is_trading_time():
                        # 如果在交易时间内，每分钟检查一次
                        next_check = now + timedelta(minutes=1)
                    else:
                        # 如果不在交易时间内，每5分钟检查一次
                        next_check = now + timedelta(minutes=5)
                        
                    wait_seconds = (next_check - now).total_seconds()
                    logger.info(f"下次检查时间: {next_check.strftime('%H:%M:%S')}，等待 {wait_seconds:.0f} 秒")
                    
                else:
                    logger.info("今天不是交易日，跳过检查")
                    # 非交易日，每小时检查一次
                    next_check = now + timedelta(hours=1)
                    wait_seconds = (next_check - now).total_seconds()
                    logger.info(f"下次检查时间: {next_check.strftime('%H:%M:%S')}，等待 {wait_seconds:.0f} 秒")
                    
                # 等待
                time.sleep(min(wait_seconds, 60))  # 最多等待60秒，以便及时响应信号
                
            except KeyboardInterrupt:
                logger.info("收到键盘中断")
                break
            except Exception as e:
                logger.error(f"调度器异常: {e}")
                time.sleep(60)  # 异常后等待1分钟再试
                
        logger.info("智能调度器退出")
        self.stop_monitor()

if __name__ == "__main__":
    scheduler = TradingScheduler()
    scheduler.run()