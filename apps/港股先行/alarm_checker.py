#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
警报检查器 - 实时监控警报状态
"""

import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import os

def check_latest_alarm():
    """检查最新警报"""
    alarm_file = Path("logs/latest_alarm.txt")
    history_file = Path("logs/alarm_history.json")
    
    print("=== 警报状态检查器 ===")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查最新警报文件
    if alarm_file.exists():
        try:
            with open(alarm_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 获取文件修改时间
            mtime = datetime.fromtimestamp(alarm_file.stat().st_mtime)
            time_ago = datetime.now() - mtime
            
            print("🚨 最新警报:")
            print(f"时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')} ({(time_ago.total_seconds() / 60):.1f} 分钟前)")
            print("内容:")
            print(content)
            print()
            
            # 如果警报很新，播放提示音
            if time_ago.total_seconds() < 300:  # 5分钟内
                print("⚠️  检测到新警报！")
                
        except Exception as e:
            print(f"读取警报文件失败: {e}")
    else:
        print("ℹ️ 暂无最新警报文件")
    
    # 检查警报历史
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if history:
                print("📊 最近警报历史:")
                # 显示最近5条
                recent = history[-5:]
                for i, record in enumerate(reversed(recent), 1):
                    print(f"{i}. {record['timestamp']} - {record['description']}")
                print()
                
                # 统计今日警报
                today = datetime.now().date()
                today_alarms = [r for r in history 
                              if datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S').date() == today]
                
                if today_alarms:
                    print(f"📈 今日警报统计: {len(today_alarms)} 次")
                    # 按条件统计
                    cond1 = len([r for r in today_alarms if r['condition_num'] == 1])
                    cond2 = len([r for r in today_alarms if r['condition_num'] == 2])
                    cond3 = len([r for r in today_alarms if r['condition_num'] == 3])
                    print(f"条件1: {cond1} 次, 条件2: {cond2} 次, 条件3: {cond3} 次")
                else:
                    print("📈 今日暂无警报")
                    
        except Exception as e:
            print(f"读取警报历史失败: {e}")
    else:
        print("ℹ️ 暂无警报历史")
    
    # 检查监控状态
    pid_file = Path("monitor.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # 检查进程是否存在
            if os.path.exists(f"/proc/{pid}"):
                print(f"✅ 监控程序正在运行 (PID: {pid})")
            else:
                print(f"❌ 监控程序PID文件存在但进程不存在")
        except:
            print("⚠️  无法检查监控程序状态")
    else:
        print("ℹ️ 监控程序未运行")

def monitor_alarms():
    """持续监控警报"""
    print("=== 实时警报监控器 ===")
    print("按 Ctrl+C 退出")
    print()
    
    last_alarm_time = None
    
    while True:
        try:
            alarm_file = Path("logs/latest_alarm.txt")
            
            if alarm_file.exists():
                # 获取文件修改时间
                mtime = datetime.fromtimestamp(alarm_file.stat().st_mtime)
                
                # 如果是新警报
                if last_alarm_time is None or mtime > last_alarm_time:
                    last_alarm_time = mtime
                    
                    # 读取警报内容
                    try:
                        with open(alarm_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        print("\n" + "="*60)
                        print("🚨 新警报触发！")
                        print(f"时间: {mtime.strftime('%H:%M:%S')}")
                        print("内容:")
                        print(content)
                        print("="*60)
                        
                        # 播放提示音
                        if os.name == 'nt':  # Windows
                            try:
                                import winsound
                                winsound.Beep(1000, 500)
                            except:
                                pass
                        
                    except Exception as e:
                        print(f"读取警报失败: {e}")
            
            # 显示运行状态
            print(f"\r监控中... {datetime.now().strftime('%H:%M:%S')} (按 Ctrl+C 退出)", end="")
            
            time.sleep(5)  # 每5秒检查一次
            
        except KeyboardInterrupt:
            print("\n\n监控已停止")
            break
        except Exception as e:
            print(f"\n监控出错: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_alarms()
    else:
        check_latest_alarm()
        print("\n提示:")
        print("- 运行 'python alarm_checker.py monitor' 进入实时监控模式")
        print("- 警报文件保存在: logs/latest_alarm.txt")
        print("- 警报历史保存在: logs/alarm_history.json")