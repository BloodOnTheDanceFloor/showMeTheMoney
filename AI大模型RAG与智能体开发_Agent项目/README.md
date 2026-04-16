# 智扫通 - 扫地机器人智能客服系统

基于 LangChain 和 ReAct 架构的智能客服系统，专为扫地机器人产品提供智能问答服务。系统集成了 RAG 检索增强生成、多工具调用和流式响应功能。

## 项目结构

```
AI大模型RAG与智能体开发_Agent项目/
├── app.py                          # Streamlit Web 应用入口
│
├── agent/                          # Agent 智能体模块
│   ├── react_agent.py              # ReAct Agent 核心实现
│   └── tools/                      # 工具函数集合
│       ├── agent_tools.py          # 工具函数定义（RAG、天气、用户信息等）
│       └── middleware.py           # 中间件（监控、日志、提示词切换）
│
├── rag/                            # RAG 检索增强生成模块
│   ├── rag_service.py              # RAG 总结服务
│   └── vector_store.py             # 向量存储服务（ChromaDB）
│
├── model/                          # 模型管理
│   └── factory.py                  # 模型工厂（统一封装模型创建）
│
├── config/                         # 配置文件目录
│   ├── agent.yml                   # Agent 配置
│   ├── rag.yml                     # RAG 配置
│   ├── chroma.yml                  # ChromaDB 配置
│   └── prompts.yml                 # 提示词配置
│
├── prompts/                        # 提示词文件
│   ├── main_prompt.txt             # Agent 主提示词
│   ├── rag_summarize.txt           # RAG 总结提示词
│   └── report_prompt.txt           # 报告生成提示词
│
├── data/                           # 知识库文档
│   ├── 扫地机器人100问.pdf         # PDF 格式知识库
│   ├── 扫地机器人100问2.txt        # TXT 格式知识库
│   ├── 扫拖一体机器人100问.txt     # 扫拖一体机知识库
│   ├── 选购指南.txt                # 选购指南文档
│   ├── 维护保养.txt                # 维护保养文档
│   ├── 故障排除.txt                # 故障排除文档
│   └── external/                   # 外部数据
│       └── records.csv             # 用户记录数据
│
├── utils/                          # 工具类
│   ├── config_handler.py           # 配置处理器
│   ├── file_handler.py             # 文件处理器
│   ├── logger_handler.py           # 日志处理器
│   ├── path_tool.py                # 路径工具
│   └── prompt_loader.py            # 提示词加载器
│
├── chroma_db/                      # ChromaDB 向量数据库（自动生成）
│   └── chroma.sqlite3
│
├── rag/chroma_db/                  # RAG 模块向量数据库（自动生成）
│   └── ...
│
├── agent/chroma_db/                # Agent 模块向量数据库（自动生成）
│   └── chroma.sqlite3
│
├── requirements.txt                # 项目依赖
└── README.md                       # 项目说明
```

## 功能特性

### 1. RAG 检索增强生成
- 基于 ChromaDB 向量数据库的知识检索
- 支持 PDF、TXT 等多种文档格式
- 自动文档分割和向量化存储
- 智能上下文组装和答案生成

### 2. ReAct Agent 架构
- 支持多步骤推理和工具调用
- 动态决策选择合适工具
- 支持流式输出，实时显示思考过程

### 3. 多工具集成
| 工具名称 | 功能说明 |
|---------|---------|
| `rag_summarize` | RAG 知识库问答 |
| `get_weather` | 获取天气信息 |
| `get_user_location` | 获取用户位置 |
| `get_user_id` | 获取用户ID |
| `get_current_month` | 获取当前月份 |
| `fetch_external_data` | 获取外部数据（CSV） |
| `fill_context_for_report` | 填充报告上下文 |

### 4. 中间件支持
- **monitor_tool**: 工具调用监控
- **log_before_model**: 模型调用前日志记录
- **report_prompt_switch**: 报告生成提示词切换

### 5. Streamlit Web 界面
- 友好的聊天界面
- 支持对话历史显示
- 流式响应展示

## 环境准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

创建 `.env` 文件或在环境变量中设置：

```bash
# 阿里云通义千问
DASHSCOPE_API_KEY=your-api-key

# 或 OpenAI
OPENAI_API_KEY=your-api-key
```

### 3. 准备 Ollama 本地模型（可选）

如果使用本地模型：

```bash
# 安装 Ollama
# 下载地址: https://ollama.com

# 拉取模型
ollama pull qwen3:4b

# 启动服务
ollama serve
```

## 使用说明

### 启动智能客服系统

```bash
streamlit run app.py
```

浏览器将自动打开 `http://localhost:8501`

### 使用示例

1. **产品咨询**
   ```
   用户: 扫地机器人怎么选购？
   助手: [调用 RAG 工具，从选购指南中检索信息并回答]
   ```

2. **故障排查**
   ```
   用户: 机器人充不进电怎么办？
   助手: [调用 RAG 工具，从故障排除文档中检索解决方案]
   ```

3. **生成报告**
   ```
   用户: 给我生成我的使用报告
   助手: [调用 fill_context_for_report 和 fetch_external_data 工具]
   ```

## 配置说明

### agent.yml
```yaml
external_data_path: data/external/records.csv
```

### chroma.yml
配置向量数据库参数，如集合名称、嵌入模型等。

### prompts.yml
配置各类提示词参数。

## 核心组件说明

### ReactAgent (agent/react_agent.py)
ReAct Agent 的核心实现，负责：
- 初始化 Agent 和工具
- 处理用户输入
- 管理对话流程
- 流式输出响应

### RagSummarizeService (rag/rag_service.py)
RAG 服务，负责：
- 向量检索
- 上下文组装
- 答案生成

### VectorStoreService (rag/vector_store.py)
向量存储服务，负责：
- 文档加载和分割
- 向量化存储
- 相似度检索

## 注意事项

1. **首次运行**：系统会自动构建向量数据库，可能需要一些时间处理知识库文档

2. **超时设置**：如果使用本地 Ollama 模型，建议在配置中设置较长的超时时间

3. **向量数据库**：
   - 数据存储在 `chroma_db/` 和 `rag/chroma_db/` 目录
   - 首次运行会自动创建，无需手动初始化
   - 更新知识库后需要重新构建向量库

4. **模型选择**：
   - 阿里云：`qwen-turbo`, `qwen-plus`, `qwen-max`
   - Ollama 本地：`qwen3:4b`, `llama3` 等

## 扩展开发

### 添加新工具

在 `agent/tools/agent_tools.py` 中添加：

```python
@tool
def my_new_tool(param: str) -> str:
    """工具描述，Agent 会根据这个描述决定何时使用"""
    # 实现逻辑
    return result
```

然后在 `react_agent.py` 中注册工具。

### 添加新知识库

1. 将文档放入 `data/` 目录
2. 在 `vector_store.py` 中配置文档路径
3. 删除旧的向量数据库文件（如有需要）
4. 重新运行系统，自动构建新的向量库

## 技术栈

- **LangChain**: LLM 应用开发框架
- **ChromaDB**: 向量数据库
- **Streamlit**: Web 应用界面
- **OpenAI API**: 大语言模型接口
- **PyYAML**: 配置文件管理
