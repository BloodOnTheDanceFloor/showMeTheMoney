@echo off
echo 正在删除Windows任务计划程序...
echo.

set TASK_NAME=港股先行监控程序

:: 删除启动任务
schtasks /delete /tn "%TASK_NAME%_Start" /f

:: 删除停止任务
schtasks /delete /tn "%TASK_NAME%_Stop" /f

echo.
echo 任务计划程序已删除！
echo.
pause