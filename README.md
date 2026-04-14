# 股票分析工具集（PNF + 交易复盘 + AI大模型RAG与智能体）

本仓库包含五个模块：
- PNF 点数图（桌面 GUI）
- 交易复盘（数据解析、FIFO撮合、报表与前端仪表盘）
- CSRC 处罚决定书下载（命令行脚本）
- AI大模型RAG与智能体开发（教程与示例代码）
- AI大模型RAG与智能体开发_Agent项目（扫地机器人智能客服完整项目）

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

AI大模型RAG与智能体开发/
  P1_OpenAI库的基础使用/    # OpenAI API 基础教程
  P2_提示词优化/              # 提示词工程案例
  P3_LangChainRAG开发/        # LangChain 核心功能
  P4_RAG项目案例/             # 完整 RAG 项目
  P5_Agent智能体/             # Agent 智能体开发

AI大模型RAG与智能体开发_Agent项目/
  app.py                      # Streamlit 应用入口
  agent/
    react_agent.py            # ReAct Agent 核心
    tools/
      agent_tools.py          # 工具函数
      middleware.py           # 中间件
  rag/
    rag_service.py            # RAG 服务
    vector_store.py           # 向量存储
  model/factory.py            # 模型工厂
  config/                     # 配置文件
  prompts/                    # 提示词文件
  data/                       # 知识库文档
  utils/                      # 工具类
```

---

## 模块三：CSRC 处罚决定书下载（命令行）

功能：从巨潮资讯网检索“证监会行政处罚决定书”，批量下载附件并按年份分类保存。

使用方法：
- 安装依赖：`pip install -r requirements.txt`
- 运行示例：
  - 下载全部页（直到无数据）：
    - `python -m apps.csrc_penalties.cli`
  - 指定最大页数与输出目录，避免过快请求设置延迟：
    - `python -m apps.csrc_penalties.cli --max-pages 10 --out e:\\downloads\\csrc --delay 0.5`
  - 自定义关键字搜索：
    - `python -m apps.csrc_penalties.cli --query "证监会行政处罚决定书"`

说明：
- 默认输出目录：`apps/csrc_penalties/downloads/<年份>/<标题>.<扩展名>`。
- 标题会自动清洗非法字符；若已存在同名文件，默认跳过（可加 `--no-skip-existing` 不跳过）。
- 接口返回的附件字段可能为 `adjunctUrl/attachPath/pdfUrl` 中之一，脚本会自动拼接到 `http://static.cninfo.com.cn/` 下载。

### 常见问题（FAQ）
- 访问页面报错 `Chart is not defined`：请确保 `index.html` 通过 CDN 引入了 `Chart.js` 与 `chartjs-plugin-zoom`，或使用本地服务器 `http.server` 访问页面（直接双击可能存在跨域与 MIME 限制）。
- 页面点击“每月盈亏”无响应：请确认 `assets/index.js` 已加载、浏览器控制台无报错、`reports/data/monthly.json` 存在且格式正确。
- 个股详情无数据：请检查 `reports/data/stock/<code>.json` 是否存在（由后端生成）。

---

## 模块四：AI大模型RAG与智能体开发（教程与示例代码）

本项目是一个系统化的 AI 大模型开发教程，涵盖从基础到进阶的完整学习路径。

### 内容结构

**P1_OpenAI库的基础使用**
- API Key 测试与配置
- OpenAI 库基础调用
- 流式输出实现
- 附带历史消息的模型调用

**P2_提示词优化**
- 金融文本分类案例
- JSON 基础使用
- 金融信息抽取案例
- 金融文本匹配判断案例

**P3_LangChain RAG开发**
- LangChain 访问阿里云通义千问/Ollama 本地模型
- 流式输出与聊天模型调用
- 嵌入模型访问（阿里云/Ollama）
- 提示词模板（通用模板、FewShot、ChatPromptTemplate）
- Chain 基础使用与 Runnable 接口
- 输出解析器（StrOutputParser、JsonOutputParser）
- 会话记忆（临时/长期）
- 文档加载器（CSV、JSON、PDF、Text）
- 向量存储（内存/持久化）
- 向量检索与提示词构建

**P4_RAG项目案例**
- 完整的 RAG 问答系统实现
- 知识库管理
- 文件上传与历史记录
- Streamlit 交互界面

**P5_Agent智能体**
- Agent 智能体初体验
- Stream 流式输出
- ReAct 案例实现
- 中间件开发

### 运行方式

```bash
# 进入对应章节目录
cd "AI大模型RAG与智能体开发/P3_LangChainRAG开发"

# 运行示例
python 14Chain的基础使用.py
```

---

## 模块五：AI大模型RAG与智能体开发_Agent项目（扫地机器人智能客服）

基于 LangChain 和 ReAct 架构的完整智能客服系统，专为扫地机器人产品提供智能问答服务。

### 功能特性

- **RAG 检索增强生成**：基于向量数据库的知识检索与答案生成
- **ReAct Agent 架构**：支持工具调用和推理决策
- **多工具集成**：天气查询、用户定位、外部数据获取等
- **流式响应**：实时输出回答内容
- **Streamlit Web 界面**：友好的交互式聊天界面
- **中间件支持**：工具监控、日志记录、提示词切换

### 项目结构

```
AI大模型RAG与智能体开发_Agent项目/
├── app.py                    # Streamlit 应用入口
├── agent/
│   ├── react_agent.py        # ReAct Agent 核心实现
│   └── tools/
│       ├── agent_tools.py    # 工具函数集合
│       └── middleware.py     # 中间件实现
├── rag/
│   ├── rag_service.py        # RAG 总结服务
│   └── vector_store.py       # 向量存储服务
├── model/
│   └── factory.py            # 模型工厂
├── config/
│   ├── agent.yml             # Agent 配置
│   ├── rag.yml               # RAG 配置
│   ├── chroma.yml            # ChromaDB 配置
│   └── prompts.yml           # 提示词配置
├── prompts/
│   ├── main_prompt.txt       # 主提示词
│   ├── rag_summarize.txt     # RAG 总结提示词
│   └── report_prompt.txt     # 报告生成提示词
├── data/                     # 知识库文档
│   ├── 扫地机器人100问.pdf
│   ├── 选购指南.txt
│   ├── 维护保养.txt
│   └── 故障排除.txt
└── utils/                    # 工具类
```

### 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动智能客服：
```bash
cd "AI大模型RAG与智能体开发_Agent项目"
streamlit run app.py
```

3. 在浏览器中访问 `http://localhost:8501` 开始使用

### 核心工具函数

- `rag_summarize`: RAG 知识库问答
- `get_weather`: 获取天气信息
- `get_user_location`: 获取用户位置
- `get_user_id`: 获取用户ID
- `get_current_month`: 获取当前月份
- `fetch_external_data`: 获取外部数据
- `fill_context_for_report`: 填充报告上下文

---

## 冗余文件检查（对照代码与README）

- `apps/trade_review/reports/assets`：包含 `index.js`、`stock.js`、`style.css`，均为前端必须文件；未使用本地 `chart.min.js`，已改为 CDN 引用，无冗余。
- `apps/trade_review/reports/data`：包含 `overall.json`, `monthly.json`, `stocks.json`, `trades.json`，以及 `stock/*.json`；如可解析持仓，还包含 `positions.json` 与 `positions_timeseries.json`，均被前端引用（仪表盘与环形图）。
- `apps/trade_review/reports/trade_review.html`：后端生成的静态报告（简版）。若仅使用交互式仪表盘，可选择不用该文件，但 GUI 默认生成它，建议保留。
- 综上：当前仓库中未发现明显冗余或多余文件；如需“精简仅保留仪表盘”，可将 `trade_review.html` 标记为可选。

---

## 依赖说明与核对（requirements.txt）

### 基础依赖（股票分析模块）

`requirements.txt`：
```
pandas
matplotlib
numpy
openpyxl
xlrd
requests
pytest
```

- `pandas`/`numpy`：数据读取与处理。
- `openpyxl`/`xlrd`：读取 `.xlsx`/`.xls`（pandas 通过这些引擎）。
- `matplotlib`：后端生成基础可视化（用于 `trade_review.html` 简版报告）。
- `requests`：CSRC 处罚决定书下载脚本的网络请求。
- `pytest`：可选的测试框架（如需为后端逻辑编写单元测试）。
- 桌面 GUI 使用 `tkinter`，为标准库无需额外安装。
- 前端使用 Chart.js（CDN），无需写入 `requirements.txt`。

### AI大模型RAG与智能体开发依赖

模块四和模块五需要以下额外依赖：

```
langchain
langchain-community
langchain-openai
chromadb
streamlit
pypdf
```

- `langchain` / `langchain-community` / `langchain-openai`：LangChain 框架及扩展
- `chromadb`：向量数据库存储
- `streamlit`：Web 应用界面
- `pypdf`：PDF 文档解析

### 完整依赖安装

```bash
# 安装所有依赖
pip install -r requirements.txt

# 单独安装 AI 模块依赖
pip install langchain langchain-community langchain-openai chromadb streamlit pypdf
```

### 版本建议

如需固定版本或增强可重复性：
```
pandas>=2.0
matplotlib>=3.7
numpy>=1.24
openpyxl>=3.1
xlrd>=2.0
requests>=2.31
pytest>=7.0
langchain>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.2.0
chromadb>=0.5.0
streamlit>=1.40.0
pypdf>=5.0.0
```
（视你的环境与兼容性需求选择是否加版本约束）

---

## 备注
- 如需自定义交易复盘输出路径：`python -m apps.trade_review.trade_review -i <excel> -o <html输出路径>`。
- 前端页面完全静态，无需后端服务；只要生成了 `reports/data/*.json` 即可工作。
- 若要扩展分类（如 GC/回购），建议在后端导出 JSON 时新增字段维度，并在前端增加筛选与分组展示。
- AI 模块需要配置 API Key（阿里云通义千问或 OpenAI），请在环境变量或配置文件中设置。
- Agent 项目首次运行时会自动构建向量数据库，可能需要一些时间处理知识库文档。