#!/bin/bash
# Docker本地构建脚本（无需联网）

echo "=== Docker本地构建方案 ==="
echo "由于网络连接问题，我们提供以下替代方案："
echo ""

# 检查是否有Python环境
echo "1. 直接使用Python环境运行（推荐）:"
echo "   python smart_scheduler.py"
echo ""

echo "2. 使用虚拟环境:"
echo "   python -m venv venv"
echo "   source venv/bin/activate  # Linux/Mac"
echo "   venv\Scripts\activate      # Windows"
echo "   pip install -r requirements.txt"
echo "   python smart_scheduler.py"
echo ""

echo "3. 使用Windows任务计划程序:"
echo "   运行 scripts/setup_task_scheduler.bat"
echo ""

echo "4. 如果一定要Docker，可以:"
echo "   - 使用本地Python镜像"
echo "   - 或者先在有网络的环境构建镜像"
echo "   - 然后导出/导入到本机"
echo ""

echo "=== 当前系统状态 ==="
python --version 2>/dev/null || echo "Python未安装"
python3 --version 2>/dev/null || echo "Python3未安装"
docker --version 2>/dev/null || echo "Docker未安装"

echo ""
echo "推荐使用方案1：直接运行Python程序！"