# 股票分析工具集（PNF + 交易复盘）

本仓库包含两个模块：
- PNF 点数图（桌面 GUI）
- 交易复盘（数据解析、FIFO撮合、报表与前端仪表盘）

---

## 模块一：PNF 点数图（GUI）

- Tkinter 桌面界面，交互式生成点数图（1点图/3点图）。
- 支持 `.xlsx`/`.xls` 数据输入，自动校正列名与数据类型。
- 格值选择（预设/固定值）、反转格数设置、悬停显示标记元信息。
- 支持保存 PNG 图片。

运行：
- 安装依赖：`pip install -r requirements.txt`
- 启动 GUI：`python -m apps.pnf.pnf_gui`

---

## 模块二：交易复盘（报表 + 前端仪表盘）

后端：从成交 Excel 解析与清洗字段，按股票进行 FIFO 撮合，按每次卖出统计已实现盈亏、持仓天数、收益率等；汇总个股与总体指标（胜率、最大回撤、平均持仓天数、平均收益率等）。

前端（纯静态页面，Chart.js 图表）：
- 仪表盘 `index.html`
- 个股详情 `stock.html`

### 新增功能概览（前端）
- 总体概览（Overall Summary）：总盈亏、交易总笔数、总胜率、盈亏比例（笔数）、交易股票数量。
- 每月盈亏柱状图（Monthly PnL）：支持缩放/拖拽；点击任意月份，页面下方“当月概览”自动切换到该月份并刷新相关数据。
- 当月概览（Top Summary）：展示当月交易总额（近似）、盈亏比例（笔数）、活跃股票数量。
- 交易记录时间轴（按日分组）：每日盈亏柱状图；点击某一天弹出当日成交详情（模态框）。
- 持仓分布环形图：按所选月份统计各股票的持仓数量占比（自动跟随月份切换）。
- 盈利变化趋势（Profit Trend）：按卖出日计算的每日盈亏与累计盈亏趋势。
- 个股交易汇总表：支持表头点击排序；可跳转到个股详情页。
- 月度交易记录列表：列出各月份的个股盈亏“标签”。
- 主题与字体：支持“浅色/深色”主题切换与 `A+ / A-` 字体大小调整（本地持久化）。

### 快速开始（命令行）
1. 安装依赖：
   - `pip install -r requirements.txt`
2. 生成数据与报表：
   - `python -m apps.trade_review.trade_review -i e:\codes\stock\PNF\成交报告单.xlsx`
   - 默认输出：`apps/trade_review/reports/trade_review.html`
   - JSON 输出：`apps/trade_review/reports/data/*.json`（包含 `overall.json`, `monthly.json`, `stocks.json`, `trades.json`, 以及 `data/stock/<code>.json`，若可解析持仓，还包含 `positions.json`, `positions_timeseries.json`）
3. 本地预览前端：
   - 在 `apps/trade_review/reports` 目录启动本地服务器：`python -m http.server 8000`
   - 打开浏览器访问：
     - 仪表盘：`http://localhost:8000/index.html`
     - 个股详情：`http://localhost:8000/stock.html?code=<股票代码>`

### 快速开始（桌面 GUI）
- 运行：`python -m apps.trade_review.trade_review_gui`
- 选择 `成交报告单.xlsx`，设置输出路径（默认：模块内 `reports/trade_review.html`）。
- 点击“生成报告”，完成后可使用“打开输出目录”查看生成的 HTML 与 JSON；在 `reports` 目录下启动 `http.server` 进行前端预览。

### 数据结构（前端依赖）
- `reports/data/trades.json`：按卖出日闭合的交易（每一笔卖出对应一条记录）。
- `reports/data/stocks.json`：个股汇总（总盈亏、胜率、最大盈亏、平均持仓天数、平均收益率等）。
- `reports/data/monthly.json`：按月份聚合后的盈亏与统计（用于“每月盈亏”与“月度交易记录”）。
- `reports/data/overall.json`：总体汇总指标（用于“总体概览”）。
- `reports/data/positions.json`（可选）：当月持仓快照（用于“持仓分布”）。
- `reports/data/positions_timeseries.json`（可选）：持仓时序数据（目前用于月度筛选）。
- `reports/data/stock/<code>.json`：个股详情页的数据载荷（包含 trades 与原始记录 raw_records）。

### 前端技术说明
- 图表：Chart.js（通过 CDN 引入），支持鼠标滚轮缩放与拖拽平移（chartjs-plugin-zoom）。
- 页面为纯静态文件，直接依赖上述 JSON 数据；无后端服务。
- 主题切换与字体大小调整通过 CSS 变量实现，并持久化到 `localStorage`。

### 目录结构
```
apps/
  pnf/
    __init__.py
    pnf_chart.py      # PNF图表核心逻辑
    pnf_gui.py        # PNF桌面GUI入口（python -m apps.pnf.pnf_gui）
  trade_review/
    __init__.py
    trade_review.py   # 交易复盘脚本入口（python -m apps.trade_review.trade_review）
    trade_review_gui.py  # 交易复盘桌面GUI入口
    reports/
      index.html      # 前端仪表盘
      stock.html      # 个股详情页
      trade_review.html  # 后端生成的简版HTML报告
      assets/
        style.css
        index.js
        stock.js
      data/           # 由 trade_review.py 运行时生成的 JSON 输出
```

### 常见问题（FAQ）
- 访问页面报错 `Chart is not defined`：请确保 `index.html` 通过 CDN 引入了 `Chart.js` 与 `chartjs-plugin-zoom`，或使用本地服务器 `http.server` 访问页面（直接双击可能存在跨域与 MIME 限制）。
- 页面点击“每月盈亏”无响应：请确认 `assets/index.js` 已加载、浏览器控制台无报错、`reports/data/monthly.json` 存在且格式正确。
- 个股详情无数据：请检查 `reports/data/stock/<code>.json` 是否存在（由后端生成）。

---

## 冗余文件检查（对照代码与README）

- `apps/trade_review/reports/assets`：包含 `index.js`、`stock.js`、`style.css`，均为前端必须文件；未使用本地 `chart.min.js`，已改为 CDN 引用，无冗余。
- `apps/trade_review/reports/data`：包含 `overall.json`, `monthly.json`, `stocks.json`, `trades.json`，以及 `stock/*.json`；如可解析持仓，还包含 `positions.json` 与 `positions_timeseries.json`，均被前端引用（仪表盘与环形图）。
- `apps/trade_review/reports/trade_review.html`：后端生成的静态报告（简版）。若仅使用交互式仪表盘，可选择不用该文件，但 GUI 默认生成它，建议保留。
- 综上：当前仓库中未发现明显冗余或多余文件；如需“精简仅保留仪表盘”，可将 `trade_review.html` 标记为可选。

---

## 依赖说明与核对（requirements.txt）

`requirements.txt`：
```
pandas
matplotlib
numpy
openpyxl
xlrd
```

- `pandas`/`numpy`：数据读取与处理。
- `openpyxl`/`xlrd`：读取 `.xlsx`/`.xls`（pandas 通过这些引擎）。
- `matplotlib`：后端生成基础可视化（用于 `trade_review.html` 简版报告）。
- 桌面 GUI 使用 `tkinter`，为标准库无需额外安装。
- 前端使用 Chart.js（CDN），无需写入 `requirements.txt`。

结论：当前 `requirements.txt` 与代码匹配、可用，无需调整。

如需固定版本或增强可重复性，可建议：
```
pandas>=2.0
matplotlib>=3.7
numpy>=1.24
openpyxl>=3.1
xlrd>=2.0
```
（视你的环境与兼容性需求选择是否加版本约束）

---

## 备注
- 如需自定义交易复盘输出路径：`python -m apps.trade_review.trade_review -i <excel> -o <html输出路径>`。
- 前端页面完全静态，无需后端服务；只要生成了 `reports/data/*.json` 即可工作。
- 若要扩展分类（如 GC/回购），建议在后端导出 JSON 时新增字段维度，并在前端增加筛选与分组展示。