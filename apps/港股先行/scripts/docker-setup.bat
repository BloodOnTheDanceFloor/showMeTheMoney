@echo off
echo 正在设置Docker容器...
echo.

:: 停止并删除现有容器
echo 停止现有容器...
docker-compose down

:: 构建镜像
echo 构建Docker镜像...
docker-compose build

:: 启动容器
echo 启动容器...
docker-compose up -d

:: 查看状态
echo.
echo 容器状态：
docker-compose ps

echo.
echo Docker容器设置完成！
echo.
echo 查看日志：
echo docker-compose logs -f
echo.
echo 停止容器：
echo docker-compose down
echo.
pause