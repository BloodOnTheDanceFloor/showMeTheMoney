@echo off
echo 正在启动智能调度器...
echo.

:: 设置Python路径
set PYTHON_PATH=python

:: 设置脚本路径
set SCRIPT_PATH=%~dp0..\smart_scheduler.py

:: 创建日志目录
if not exist logs mkdir logs

:: 启动调度器
echo 启动智能调度器...
echo 交易时间: 每个交易日 09:15 - 10:30
echo 日志文件: logs/scheduler.log
echo.

%PYTHON_PATH% "%SCRIPT_PATH%"

echo.
echo 调度器已停止
echo.
pause