#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
警报管理器 - 支持多种通知方式
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import platform

try:
    import winsound  # Windows系统
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# 设置日志
logger = logging.getLogger(__name__)

class AlarmManager:
    def __init__(self):
        self.alarm_log_file = Path("logs/alarm_history.json")
        self.alarm_log_file.parent.mkdir(exist_ok=True)
        self.alarm_history = self.load_alarm_history()
        
    def load_alarm_history(self):
        """加载警报历史"""
        if self.alarm_log_file.exists():
            try:
                with open(self.alarm_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载警报历史失败: {e}")
                return []
        return []
        
    def save_alarm_history(self):
        """保存警报历史"""
        try:
            with open(self.alarm_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.alarm_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存警报历史失败: {e}")
            
    def add_alarm_record(self, condition_num, description, details):
        """添加警报记录"""
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'condition_num': condition_num,
            'description': description,
            'details': details
        }
        self.alarm_history.append(record)
        # 只保留最近100条记录
        self.alarm_history = self.alarm_history[-100:]
        self.save_alarm_history()
        
    def play_beep_sound(self, frequency=1000, duration=1000):
        """播放提示音"""
        try:
            if HAS_WINSOUND and platform.system() == 'Windows':
                winsound.Beep(frequency, duration)
            else:
                # Linux/Mac 使用系统命令
                if platform.system() == 'Linux':
                    subprocess.run(['beep'], check=False)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'], check=False)
        except Exception as e:
            logger.error(f"播放提示音失败: {e}")
            
    def show_console_notification(self, message):
        """控制台通知"""
        print("\n" + "="*60)
        print("🚨 警报触发！")
        print("="*60)
        print(message)
        print("="*60 + "\n")
        
    def create_alarm_file(self, message):
        """创建警报文件（Docker环境用）"""
        alarm_file = Path("logs/latest_alarm.txt")
        try:
            with open(alarm_file, 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"警报内容:\n{message}\n")
            logger.info(f"警报文件已创建: {alarm_file}")
        except Exception as e:
            logger.error(f"创建警报文件失败: {e}")
            
    def send_notification(self, condition_num, description, suggestion, win_rate, window_min, thresholds):
        """
        发送通知 - 根据环境选择合适的方式
        """
        # 格式化消息
        message = f"""
条件{condition_num}触发：{description}！
建议: {suggestion}
历史胜率: {win_rate:.1f}%
窗口: {window_min}分钟
阈值: {thresholds}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 记录警报历史
        self.add_alarm_record(condition_num, description, message.strip())
        
        # 控制台通知（总是显示）
        self.show_console_notification(message)
        
        # 创建警报文件（供外部检查）
        self.create_alarm_file(message)
        
        # 尝试播放提示音
        self.play_beep_sound()
        
        # 如果在Docker容器中，额外提示
        if os.path.exists('/.dockerenv'):
            logger.warning("检测到Docker环境，弹窗通知可能无法显示到宿主机")
            logger.info("请检查日志文件或latest_alarm.txt获取警报详情")
            
        logger.info(f"警报已发送: 条件{condition_num} - {description}")
        
    def get_recent_alarms(self, hours=24):
        """获取最近指定小时内的警报"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alarms = []
        
        for record in self.alarm_history:
            try:
                record_time = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                if record_time >= cutoff_time:
                    recent_alarms.append(record)
            except:
                continue
                
        return recent_alarms
        
    def clear_alarm_history(self):
        """清空警报历史"""
        self.alarm_history = []
        self.save_alarm_history()
        logger.info("警报历史已清空")

# 全局警报管理器实例
alarm_manager = AlarmManager()

def show_condition1_alarm(win_rate, window_min, hsi_thresh, csi300_thresh):
    """显示条件1报警"""
    description = "港股先涨为敬"
    suggestion = "A股或跟进"
    thresholds = f">{hsi_thresh}%恒指涨幅、<{csi300_thresh}%沪深300涨幅"
    alarm_manager.send_notification(1, description, suggestion, win_rate, window_min, thresholds)

def show_condition2_alarm(win_rate, window_min, hsi_thresh, hs_tech_thresh):
    """显示条件2报警"""
    description = "早盘强度高"
    suggestion = "国家队拉升概率提升"
    thresholds = f">{hsi_thresh}%恒指或>{hs_tech_thresh}%恒生科技涨幅"
    alarm_manager.send_notification(2, description, suggestion, win_rate, window_min, thresholds)

def show_condition3_alarm(win_rate, window_min, hsi_thresh, basis_thresh):
    """显示条件3报警"""
    description = "组合信号"
    suggestion = "捕捉托市行情"
    thresholds = f">{hsi_thresh}%恒指涨幅、>{basis_thresh}%基差收敛"
    alarm_manager.send_notification(3, description, suggestion, win_rate, window_min, thresholds)

if __name__ == "__main__":
    # 测试警报系统
    print("测试警报系统...")
    show_condition1_alarm(75.5, 30, 1.5, 0.5)
    time.sleep(2)
    show_condition2_alarm(68.2, 30, 1.0, 1.0)
    time.sleep(2)
    show_condition3_alarm(82.1, 30, 1.5, 0.5)
    
    print("\n最近24小时警报:")
    recent = alarm_manager.get_recent_alarms(24)
    for alarm in recent:
        print(f"- {alarm['timestamp']}: {alarm['description']}")