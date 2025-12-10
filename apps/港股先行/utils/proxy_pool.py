#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理IP池模块
提供免费的代理IP获取和管理功能
"""

import requests
import random
import time
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import threading
import concurrent.futures

logger = logging.getLogger(__name__)

class ProxyPool:
    """代理IP池管理器"""
    
    def __init__(self):
        self.proxies: List[Dict] = []
        self.valid_proxies: List[Dict] = []
        self.proxy_health: Dict[str, Dict] = {}  # 代理健康状态
        self.lock = threading.Lock()
    
    def update_proxy_health(self, proxy_url: str, healthy: bool, response_time: float):
        """
        更新代理健康状态
        
        参数:
            proxy_url: 代理URL
            healthy: 是否健康
            response_time: 响应时间
        """
        with self.lock:
            self.proxy_health[proxy_url] = {
                'healthy': healthy,
                'response_time': response_time,
                'last_check': time.time(),
                'check_count': self.proxy_health.get(proxy_url, {}).get('check_count', 0) + 1,
                'success_count': self.proxy_health.get(proxy_url, {}).get('success_count', 0) + (1 if healthy else 0)
            }
    
    def get_proxy_health(self, proxy_url: str) -> Dict:
        """
        获取代理健康状态
        
        参数:
            proxy_url: 代理URL
            
        返回:
            dict: 健康状态信息
        """
        with self.lock:
            return self.proxy_health.get(proxy_url, {
                'healthy': True,
                'response_time': 0,
                'last_check': None,
                'check_count': 0,
                'success_count': 0
            })
    
    def cleanup_stale_proxies(self, stale_hours: int = 24):
        """
        清理长时间未使用的代理
        
        参数:
            stale_hours: 过期时间（小时）
        """
        with self.lock:
            current_time = time.time()
            stale_threshold = stale_hours * 3600
            
            # 清理健康状态记录
            stale_proxies = [
                proxy for proxy, health in self.proxy_health.items()
                if health.get('last_check') and (current_time - health['last_check']) > stale_threshold
            ]
            
            for proxy in stale_proxies:
                del self.proxy_health[proxy]
                logger.info(f"清理过期代理: {proxy}")
    
    def refresh_proxies(self):
        """刷新代理池"""
        logger.info("刷新代理池...")
        self.update_proxy_pool()

    def fetch_free_proxies(self) -> List[Dict]:
        """从免费代理网站获取代理IP"""
        proxy_sites = [
            {
                'url': 'https://www.kuaidaili.com/free/inha/1/',
                'parser': self._parse_kuaidaili
            },
            {
                'url': 'https://www.89ip.cn/tqdl.html?api=1&num=20&port=&address=&isp=',
                'parser': self._parse_89ip
            },
            {
                'url': 'https://free-proxy-list.net/',
                'parser': self._parse_free_proxy_list
            },
            {
                'url': 'https://www.proxy-list.download/api/v1/get?type=http',
                'parser': self._parse_proxy_list_download
            }
        ]
        
        all_proxies = []
        
        for site in proxy_sites:
            try:
                logger.info(f"从 {site['url']} 获取代理IP...")
                headers = {
                    'User-Agent': random.choice([
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    ])
                }
                
                # 使用直连获取代理列表（不通过代理）
                response = requests.get(site['url'], headers=headers, timeout=10, verify=False)
                if response.status_code == 200:
                    proxies = site['parser'](response.text)
                    all_proxies.extend(proxies)
                    logger.info(f"从 {site['url']} 获取到 {len(proxies)} 个代理IP")
                
                # 避免过于频繁的请求
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"从 {site['url']} 获取代理IP失败: {e}")
                continue
        
        return all_proxies
    
    def _parse_kuaidaili(self, html: str) -> List[Dict]:
        """解析快代理网站"""
        proxies = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', class_='table table-bordered table-striped')
            if table:
                rows = table.find('tbody').find_all('tr')
                for row in rows[:10]:  # 只取前10个
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxies.append({
                            'http': f'http://{ip}:{port}',
                            'https': f'http://{ip}:{port}'
                        })
        except Exception as e:
            logger.error(f"解析快代理失败: {e}")
        
        return proxies
    
    def _parse_free_proxy_list(self, html: str) -> List[Dict]:
        """解析free-proxy-list.net"""
        proxies = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'id': 'proxylisttable'})
            if table:
                rows = table.find('tbody').find_all('tr')
                for row in rows[:20]:  # 限制获取前20个代理
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        https = cols[6].text.strip() if len(cols) > 6 else 'no'
                        
                        proxy_url = f'http://{ip}:{port}'
                        proxy_dict = {
                            'http': proxy_url,
                            'https': proxy_url if https.lower() == 'yes' else None
                        }
                        if proxy_dict['https'] is None:
                            del proxy_dict['https']
                        proxies.append(proxy_dict)
        except Exception as e:
            logger.error(f"解析free-proxy-list.net失败: {e}")
        
        return proxies
    
    def _parse_proxy_list_download(self, html: str) -> List[Dict]:
        """解析proxy-list.download"""
        proxies = []
        try:
            # 这个API返回的是纯文本格式，每行一个代理IP:端口
            lines = html.strip().split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        port = parts[1].strip()
                        proxies.append({
                            'http': f'http://{ip}:{port}',
                            'https': f'http://{ip}:{port}'
                        })
        except Exception as e:
            logger.error(f"解析proxy-list.download失败: {e}")
        
        return proxies
    
    def _parse_89ip(self, html: str) -> List[Dict]:
        """解析89IP网站"""
        proxies = []
        try:
            # 这个网站返回的是纯文本格式
            lines = html.strip().split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        port = parts[1].strip()
                        proxies.append({
                            'http': f'http://{ip}:{port}',
                            'https': f'http://{ip}:{port}'
                        })
        except Exception as e:
            logger.error(f"解析89IP失败: {e}")
        
        return proxies
    
    def validate_proxy(self, proxy: Dict, timeout: int = 10) -> bool:
        """验证代理是否可用"""
        try:
            test_url = 'http://httpbin.org/ip'
            response = requests.get(
                test_url, 
                proxies=proxy, 
                timeout=timeout,
                verify=False,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"代理 {proxy} 验证成功，返回IP: {result.get('origin', 'unknown')}")
                return True
            else:
                logger.debug(f"代理 {proxy} 验证失败，状态码: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.debug(f"代理 {proxy} 超时")
            return False
        except requests.exceptions.ConnectionError:
            logger.debug(f"代理 {proxy} 连接错误")
            return False
        except Exception as e:
            logger.debug(f"代理 {proxy} 验证失败: {e}")
            return False
    
    def update_proxy_pool(self):
        """更新代理IP池"""
        logger.info("开始更新代理IP池...")
        
        # 获取新的代理IP
        new_proxies = self.fetch_free_proxies()
        logger.info(f"共获取到 {len(new_proxies)} 个代理IP")
        
        # 随机选择一部分代理进行验证，避免验证所有代理耗时过长
        sample_size = min(30, len(new_proxies))  # 最多验证30个代理
        sample_proxies = random.sample(new_proxies, sample_size)
        
        # 使用线程池并发验证代理
        import concurrent.futures
        valid_proxies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {executor.submit(self.validate_proxy, proxy, 8): proxy for proxy in sample_proxies}
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        valid_proxies.append(proxy)
                        logger.info(f"✓ 代理 {proxy['http']} 有效")
                except Exception as e:
                    logger.debug(f"代理验证异常: {e}")
        
        # 更新有效代理列表
        with self.lock:
            self.valid_proxies = valid_proxies
            self.proxies = new_proxies
        
        logger.info(f"代理IP池更新完成，有效代理: {len(valid_proxies)}/{len(new_proxies)}")
    
    def get_random_proxy(self) -> Optional[Dict]:
        """获取随机可用代理"""
        with self.lock:
            if self.valid_proxies:
                return random.choice(self.valid_proxies)
        
        # 如果没有有效代理，返回None
        return None
    
    def get_proxy_stats(self) -> Dict:
        """获取代理池统计信息"""
        with self.lock:
            return {
                'total': len(self.proxies),
                'valid': len(self.valid_proxies),
                'valid_rate': len(self.valid_proxies) / len(self.proxies) if self.proxies else 0
            }

    def get_all_proxies(self) -> List[str]:
        """获取所有代理URL列表"""
        with self.lock:
            return [proxy['http'] for proxy in self.proxies]

# 全局代理池实例
proxy_pool = ProxyPool()

def get_proxy_session() -> requests.Session:
    """获取带代理的requests会话"""
    session = requests.Session()
    
    # 获取随机代理
    proxy = proxy_pool.get_random_proxy()
    if proxy:
        session.proxies.update(proxy)
        logger.info(f"使用代理: {proxy['http']}")
    else:
        logger.warning("没有可用代理，使用直连")
    
    return session