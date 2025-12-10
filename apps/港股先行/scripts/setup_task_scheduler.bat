@echo off
echo 正在设置Windows任务计划程序...
echo.

:: 设置变量
set TASK_NAME=港股先行监控程序
set SCRIPT_PATH=D:\codes\stock\showMeTheMoney\apps\港股先行\main.py
set PYTHON_PATH=D:\codes\stock\showMeTheMoney\apps\港股先行\venv\Scripts\python.exe
set START_TIME=09:15
set END_TIME=10:30

:: 删除已存在的任务（如果存在）
schtasks /delete /tn "%TASK_NAME%" /f 2>nul

:: 创建启动任务（每个交易日9:15开始）
echo 创建启动任务：%TASK_NAME%_Start
schtasks /create ^
    /tn "%TASK_NAME%_Start" ^
    /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /sc weekly ^
    /d MON,TUE,WED,THU,FRI ^
    /st %START_TIME% ^
    /f ^
    /ru SYSTEM

:: 创建停止任务（每个交易日10:30停止）
echo 创建停止任务：%TASK_NAME%_Stop
schtasks /create ^
    /tn "%TASK_NAME%_Stop" ^
    /tr "taskkill /f /im python.exe" ^
    /sc weekly ^
    /d MON,TUE,WED,THU,FRI ^
    /st %END_TIME% ^
    /f ^
    /ru SYSTEM

echo.
echo 任务计划程序设置完成！
echo 启动时间：每个交易日 %START_TIME%
echo 停止时间：每个交易日 %END_TIME%
echo.
echo 可以使用以下命令查看任务状态：
echo schtasks /query /tn "%TASK_NAME%_Start"
echo schtasks /query /tn "%TASK_NAME%_Stop"
echo.
pause