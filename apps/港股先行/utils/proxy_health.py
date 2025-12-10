#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理IP健康检查模块
"""

import time
import requests
import threading
from datetime import datetime, timedelta
from .proxy_pool import ProxyPool
from .logger import setup_logger

# 设置日志
logger = setup_logger()

class ProxyHealthChecker:
    """代理IP健康检查器"""
    
    def __init__(self, check_interval=300, timeout=10):
        """
        初始化代理健康检查器
        
        参数:
            check_interval: 检查间隔时间（秒）
            timeout: 请求超时时间（秒）
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.proxy_pool = ProxyPool()
        self.running = False
        self.check_thread = None
        
        # 测试URL列表
        self.test_urls = [
            'https://httpbin.org/ip',
            'https://api.ipify.org?format=json',
            'https://icanhazip.com'
        ]
        
        logger.info(f"代理健康检查器初始化完成，检查间隔: {check_interval}秒")
    
    def check_proxy_health(self, proxy_url):
        """
        检查单个代理的健康状态
        
        参数:
            proxy_url: 代理URL (如: http://ip:port)
            
        返回:
            dict: 检查结果 {'healthy': bool, 'response_time': float, 'error': str}
        """
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        start_time = time.time()
        
        try:
            # 随机选择一个测试URL
            test_url = self.test_urls[hash(proxy_url) % len(self.test_urls)]
            
            response = requests.get(
                test_url, 
                proxies=proxies, 
                timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.debug(f"代理 {proxy_url} 健康检查通过，响应时间: {response_time:.2f}秒")
                return {
                    'healthy': True,
                    'response_time': response_time,
                    'error': None
                }
            else:
                logger.warning(f"代理 {proxy_url} 返回状态码: {response.status_code}")
                return {
                    'healthy': False,
                    'response_time': response_time,
                    'error': f'HTTP {response.status_code}'
                }
                
        except requests.exceptions.ProxyError as e:
            logger.warning(f"代理 {proxy_url} 连接错误: {str(e)}")
            return {
                'healthy': False,
                'response_time': time.time() - start_time,
                'error': 'Proxy connection failed'
            }
        except requests.exceptions.Timeout as e:
            logger.warning(f"代理 {proxy_url} 超时: {str(e)}")
            return {
                'healthy': False,
                'response_time': time.time() - start_time,
                'error': 'Timeout'
            }
        except Exception as e:
            logger.warning(f"代理 {proxy_url} 检查失败: {str(e)}")
            return {
                'healthy': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    def check_all_proxies(self):
        """检查所有代理的健康状态"""
        logger.info("开始代理健康检查...")
        
        all_proxies = self.proxy_pool.get_all_proxies()
        healthy_count = 0
        total_count = len(all_proxies)
        
        for proxy_url in all_proxies:
            result = self.check_proxy_health(proxy_url)
            
            if result['healthy']:
                healthy_count += 1
                # 更新代理池中的代理状态
                self.proxy_pool.update_proxy_health(proxy_url, True, result['response_time'])
            else:
                # 标记为不健康，减少使用概率
                self.proxy_pool.update_proxy_health(proxy_url, False, result['response_time'])
                logger.info(f"代理 {proxy_url} 标记为不健康: {result['error']}")
        
        logger.info(f"代理健康检查完成: {healthy_count}/{total_count} 个代理健康")
        return healthy_count, total_count
    
    def health_check_worker(self):
        """健康检查工作线程"""
        while self.running:
            try:
                self.check_all_proxies()
                
                # 清理长时间未使用的代理
                self.proxy_pool.cleanup_stale_proxies()
                
                # 如果健康代理太少，重新获取
                healthy_count, total_count = self.check_all_proxies()
                if healthy_count < 5 and total_count < 20:
                    logger.info("健康代理数量不足，重新获取代理...")
                    self.proxy_pool.refresh_proxies()
                
            except Exception as e:
                logger.error(f"健康检查工作线程出错: {str(e)}")
            
            # 等待下一次检查
            time.sleep(self.check_interval)
    
    def start_health_check(self):
        """启动健康检查"""
        if self.running:
            logger.warning("健康检查已经在运行中")
            return
        
        self.running = True
        self.check_thread = threading.Thread(target=self.health_check_worker, daemon=True)
        self.check_thread.start()
        logger.info("代理健康检查已启动")
        
        # 立即执行一次检查
        self.check_all_proxies()
    
    def stop_health_check(self):
        """停止健康检查"""
        if not self.running:
            logger.warning("健康检查未运行")
            return
        
        self.running = False
        if self.check_thread and self.check_thread.is_alive():
            self.check_thread.join(timeout=5)
        logger.info("代理健康检查已停止")
    
    def get_health_status(self):
        """
        获取代理健康状态
        
        返回:
            dict: 健康状态统计
        """
        all_proxies = self.proxy_pool.get_all_proxies()
        healthy_proxies = []
        unhealthy_proxies = []
        
        for proxy_url in all_proxies:
            health_info = self.proxy_pool.get_proxy_health(proxy_url)
            if health_info.get('healthy', True):
                healthy_proxies.append({
                    'proxy': proxy_url,
                    'response_time': health_info.get('response_time', 0),
                    'last_check': health_info.get('last_check', None)
                })
            else:
                unhealthy_proxies.append({
                    'proxy': proxy_url,
                    'error': health_info.get('error', 'Unknown'),
                    'last_check': health_info.get('last_check', None)
                })
        
        return {
            'total_proxies': len(all_proxies),
            'healthy_proxies': len(healthy_proxies),
            'unhealthy_proxies': len(unhealthy_proxies),
            'healthy_list': healthy_proxies,
            'unhealthy_list': unhealthy_proxies,
            'health_rate': len(healthy_proxies) / len(all_proxies) * 100 if all_proxies else 0
        }

# 全局健康检查器实例
_health_checker = None

def get_health_checker():
    """获取全局健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = ProxyHealthChecker()
    return _health_checker

def start_proxy_health_check():
    """启动代理健康检查"""
    checker = get_health_checker()
    checker.start_health_check()
    return checker

def stop_proxy_health_check():
    """停止代理健康检查"""
    global _health_checker
    if _health_checker:
        _health_checker.stop_health_check()
        _health_checker = None

def get_proxy_health_status():
    """获取代理健康状态"""
    checker = get_health_checker()
    return checker.get_health_status()

if __name__ == '__main__':
    # 测试代理健康检查
    print("测试代理健康检查...")
    checker = ProxyHealthChecker(check_interval=60)  # 1分钟检查间隔用于测试
    
    # 执行一次检查
    healthy, total = checker.check_all_proxies()
    print(f"代理健康检查结果: {healthy}/{total} 个代理健康")
    
    # 获取详细状态
    status = checker.get_health_status()
    print(f"健康率: {status['health_rate']:.1f}%")
    
    if status['healthy_list']:
        print("健康代理列表:")
        for proxy in status['healthy_list'][:5]:  # 只显示前5个
            print(f"  - {proxy['proxy']} (响应时间: {proxy['response_time']:.2f}秒)")
    
    if status['unhealthy_list']:
        print("不健康代理列表:")
        for proxy in status['unhealthy_list'][:5]:  # 只显示前5个
            print(f"  - {proxy['proxy']} (错误: {proxy['error']})")