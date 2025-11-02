# 股票分析工具集（PNF + 交易复盘）

本仓库包含两大模块：
- PNF 点数图（桌面 GUI）
- 交易复盘（数据解析、FIFO撮合、报表与前端展示）

## 模块一：PNF 点数图（GUI）

- Tkinter 桌面界面，交互式生成点数图（1点图/3点图）。
- 支持 `.xlsx`/`.xls` 数据输入，自动校正列名与数据类型。
- 格值选择（预设/固定值）、反转格数设置、悬停显示标记元信息。
- 支持保存 PNG 图片。

运行：
- 安装依赖：`pip install -r requirements.txt`
- 启动 GUI：`python -m apps.pnf.pnf_gui`

## 模块二：交易复盘（报表 + 前端）

- 从成交 Excel 解析字段，推断方向，统一数据格式。
- 按股票进行 FIFO 撮合，按每次卖出统计已实现盈亏、持仓天数、收益率等。
- 汇总个股与总体指标（胜率、最大回撤、平均持仓天数、平均收益率等）。
- 生成 HTML 报表，并导出 JSON 以供前端仪表盘与个股详情使用。
- 前端（纯静态页面，Chart.js 图表）：仪表盘 `index.html` 与个股详情 `stock.html`。

生成数据与报表：
- 执行：`python -m apps.trade_review.trade_review -i e:\codes\stock\PNF\成交报告单.xlsx`
- 默认输出：`apps/trade_review/reports/trade_review.html`
- JSON 输出：`apps/trade_review/reports/data/*.json`（包含 `overall.json`, `monthly.json`, `stocks.json`, `trades.json`, 以及 `data/stock/<code>.json`）

本地预览前端：
- 在 `apps/trade_review/reports` 目录启动本地服务器：
  - Windows PowerShell：`python -m http.server 8000`
- 打开浏览器访问：
  - 仪表盘：`http://localhost:8000/index.html`
  - 个股详情：`http://localhost:8000/stock.html?code=600871`（示例）

## 文件结构

```
apps/
  pnf/
    __init__.py
    pnf_chart.py      # PNF图表核心逻辑
    pnf_gui.py        # PNF桌面GUI入口（python -m apps.pnf.pnf_gui）
  trade_review/
    __init__.py
    trade_review.py   # 交易复盘脚本入口（python -m apps.trade_review.trade_review）
    reports/
      index.html      # 前端仪表盘
      stock.html      # 个股详情页
      assets/
        style.css
        index.js
        stock.js
      data/           # 由 trade_review.py 运行时生成的 JSON 输出

requirements.txt      # 项目依赖库列表
成交报告单.xlsx        # 交易复盘数据源（示例）
stockXLS/              # PNF示例数据（.xls）
```

## 依赖说明

- pandas, matplotlib, numpy, openpyxl（读取 `.xlsx`）
- xlrd（读取 `.xls`，PNF 模块用到；可选）

## 备注

- 如需自定义交易复盘输出路径：`python -m apps.trade_review.trade_review -i <excel> -o <html输出路径>`。
- 前端页面完全静态，无需后端服务；只要生成了 `reports/data/*.json` 即可工作。
- 若要扩展分类（如 GC/回购），可在后端导出 JSON 时新增字段维度，并在前端增加筛选与分组展示。