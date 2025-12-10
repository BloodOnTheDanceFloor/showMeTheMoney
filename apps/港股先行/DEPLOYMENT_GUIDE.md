# 港股先行监控程序部署指南

## 方案对比

### 方案1：智能调度器（推荐）
**使用方法：**
```bash
# 直接运行智能调度器
python smart_scheduler.py

# 或使用批处理脚本
scripts\run_scheduler.bat
```

**优点：**
- ✅ 最智能的方案，自动管理程序生命周期
- ✅ 实时监控，每分钟检查是否在交易时间
- ✅ 自动重启崩溃的程序
- ✅ 日志记录完整，便于调试
- ✅ 无需管理员权限
- ✅ 支持手动停止（Ctrl+C）
- ✅ 可以后台运行

**缺点：**
- ⚠️ 需要保持命令行窗口开启
- ⚠️ 重启电脑后需要手动启动

**改进方法：**
- 将调度器添加到Windows启动项，开机自动运行
- 使用`pythonw smart_scheduler.py` 无窗口运行

---

### 方案2：Windows任务计划程序
**使用方法：**
```bash
# 以管理员身份运行
scripts\setup_task_scheduler.bat

# 查看任务状态
schtasks /query /tn "港股先行监控程序_Start"
schtasks /query /tn "港股先行监控程序_Stop"

# 删除任务
scripts\remove_task_scheduler.bat
```

**优点：**
- ✅ 完全自动化，无需人工干预
- ✅ 系统级服务，稳定可靠
- ✅ 重启后自动恢复
- ✅ 精确的时间控制

**缺点：**
- ⚠️ 需要管理员权限
- ⚠️ 配置相对复杂
- ⚠️ 调试困难（需要查看系统日志）
- ⚠️ 停止任务会kill所有python进程

---

### 方案3：Docker容器
**使用方法：**
```bash
# 启动Docker容器
scripts\docker-setup.bat

# 手动操作
docker-compose up -d
docker-compose logs -f
docker-compose down
```

**优点：**
- ✅ 环境隔离，不会污染系统
- ✅ 易于迁移和备份
- ✅ 可以结合Docker Desktop实现开机启动
- ✅ 日志管理方便

**缺点：**
- ⚠️ 需要安装Docker Desktop
- ⚠️ 资源占用相对较高
- ⚠️ 对Docker知识有要求
- ⚠️ 容器内时间同步问题
- ⚠️ 需要网络连接才能拉取镜像（可能失败）
- ⚠️ 警报弹窗无法显示到宿主机（需要额外配置）

**Docker网络问题解决方案：**
如果Docker构建失败，可以使用本地替代方案：
```bash
# 使用本地Python环境运行
python smart_scheduler.py

# 或者创建本地Python虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python smart_scheduler.py
```

---

## 推荐配置

### 最佳实践（智能调度器 + 开机启动）

1. **设置开机启动：**
   ```bash
   # 创建快捷方式到启动文件夹
   # Win+R 输入：shell:startup
   # 创建 smart_scheduler.py 的快捷方式
   ```

2. **无窗口运行：**
   ```bash
   # 修改快捷方式目标为：
   pythonw.exe D:\codes\stock\showMeTheMoney\apps\港股先行\smart_scheduler.py
   ```

3. **创建监控脚本：**
   ```bash
   # 创建 start_monitor.bat
   @echo off
   cd /d D:\codes\stock\showMeTheMoney\apps\港股先行
   start pythonw smart_scheduler.py
   ```

### 配置文件说明

**data/config.py 关键配置：**
```python
# 交易时间 (早盘监控时段：9:15-10:30)
'trading_start_time': '09:15',
'trading_end_time': '10:30',

# 检查间隔（秒）
'check_interval': 600,  # 10分钟
```

## 监控和调试

### 日志文件
- `logs/scheduler.log` - 调度器日志
- `logs/stock_monitor.log` - 监控程序日志

### 常用命令
```bash
# 查看实时日志
tail -f logs/scheduler.log

# 检查进程是否在运行
tasklist | findstr python

# 停止所有Python进程
taskkill /f /im python.exe
```

## 故障排除

### 常见问题

1. **程序没有按时启动**
   - 检查系统时间是否正确
   - 查看调度器日志
   - 确认Python路径正确

2. **Docker容器时间不对**
   - 在docker-compose.yml中添加时区设置
   - 确保宿主机时间正确

3. **任务计划程序权限问题**
   - 以管理员身份运行脚本
   - 检查任务计划程序服务是否运行

## 最终建议

**重要提醒：关于Docker网络连接问题**

由于当前环境存在Docker网络连接问题（无法拉取镜像），建议优先考虑本地Python方案。

**对于你的需求，我推荐：**

1. **主方案：** 使用智能调度器（smart_scheduler.py）直接运行
   ```bash
   python smart_scheduler.py
   ```

2. **警报监控：** 使用警报检查器实时监控
   ```bash
   # 检查最新警报
   python alarm_checker.py
   
   # 实时监控模式（推荐）
   python alarm_checker.py monitor
   ```

3. **运行方式：** 
   - 开发环境：直接运行，保持窗口开启
   - 生产环境：添加到Windows启动项，使用pythonw无窗口运行

4. **备份方案：** 
   - Windows任务计划程序（需要管理员权限）
   - Docker方案（需要网络连接）

**这样配置的优势：**
- ✅ 无需网络连接，立即可用
- ✅ 警报可见，实时监控
- ✅ 配置简单，维护方便
- ✅ 支持多种通知方式（控制台、文件、声音）