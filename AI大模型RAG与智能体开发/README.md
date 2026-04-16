# AI大模型RAG与智能体开发

本教程项目涵盖从 OpenAI API 基础使用到 LangChain RAG 开发，再到 Agent 智能体构建的完整学习路径。

## 项目结构

```
AI大模型RAG与智能体开发/
├── P1_OpenAI库的基础使用/          # OpenAI API 基础教程
│   ├── 01测试APIKEY的使用.py
│   ├── 02OpenAI库的基础使用.py
│   ├── 03OpenAI库的流式输出.py
│   └── 04OpenAI库附带历史消息调用模型.py
│
├── P2_提示词优化/                   # 提示词工程案例
│   ├── 01提示词优化案例_金融文本分类.py
│   ├── 02Json的基础使用.py
│   ├── 03提示词优化案例_金融信息抽取.py
│   ├── 04提示词优化案例_金融文本匹配判断.py
│   └── 05提示词优化案例_彩票信息抽取.py
│
├── P3_LangChainRAG开发/             # LangChain 核心功能
│   ├── 01[扩展]余弦相似度.py
│   ├── 02LangChain访问阿里云通义千问大模型.py
│   ├── 03LangChain访问Ollama本地模型.py
│   ├── 04LangChain的流式输出.py
│   ├── 05LangChain调用聊天模型.py
│   ├── 06LangChain调用Ollama的聊天模型.py
│   ├── 07LangChain消息的简写形式.py
│   ├── 08LangChain访问阿里云嵌入模型.py
│   ├── 09LangChain访问Ollama的本地嵌入模型.py
│   ├── 10通用提示词模板.py
│   ├── 11FewShot提示词模板.py
│   ├── 12模板类的format和invoke方法.py
│   ├── 13ChatPromptTemplate的使用.py
│   ├── 14Chain的基础使用.py
│   ├── 15[扩展]Python的或运算符的重写.py
│   ├── 16Runnable接口源码查看.py
│   ├── 17StrOutputParser解析器.py
│   ├── 18JsonOutputParser解析器.py
│   ├── 19RunnableLambda的基础使用.py
│   ├── 20临时会话记忆.py
│   ├── 21长期会话记忆.py
│   ├── 22CSVLoader的使用.py
│   ├── 23JSONLoader的使用.py
│   ├── 24PyPDFLoader的使用.py
│   ├── 25TextLoader和文档分割器.py
│   ├── 26内存向量存储.py
│   ├── 27外部向量持久化存储.py
│   ├── 28向量检索构建提示词.py
│   ├── 29RunnablePassthrough的使用.py
│   └── data/                        # 示例数据文件
│       ├── Python基础语法.txt
│       ├── info.csv
│       ├── stu.csv
│       ├── stu.json
│       ├── pdf1.pdf
│       └── pdf2.pdf
│
├── P4_RAG项目案例/                  # 完整 RAG 问答系统
│   ├── app_qa.py                    # 问答应用主程序
│   ├── app_file_uploader.py         # 文件上传组件
│   ├── rag.py                       # RAG 核心逻辑
│   ├── knowledge_base.py            # 知识库管理
│   ├── vector_stores.py             # 向量存储封装
│   ├── file_history_store.py        # 文件历史记录
│   ├── config_data.py               # 配置数据
│   └── data/                        # 知识库文档
│       ├── 尺码推荐.txt
│       ├── 洗涤养护.txt
│       └── 颜色选择.txt
│
├── P5_Agent智能体/                  # Agent 智能体开发
│   ├── 01Agent智能体初体验.py
│   ├── 02Agent的stream流式输出.py
│   ├── 03ReAct案例.py
│   └── 04middleware中间件.py
│
├── requirements.txt                 # 项目依赖
└── README.md                        # 项目说明
```

## 环境准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

#### 方式一：阿里云通义千问（推荐）
```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your-api-key"

# Windows CMD
set DASHSCOPE_API_KEY=your-api-key
```

#### 方式二：Ollama 本地模型
确保 Ollama 已安装并运行：
```bash
# 安装模型
ollama pull qwen3:4b

# 启动服务
ollama serve
```

## 使用说明

### P1 - OpenAI 基础
学习 OpenAI API 的基本调用方式：
```bash
cd P1_OpenAI库的基础使用
python 02OpenAI库的基础使用.py
```

### P2 - 提示词优化
掌握 Few-Shot、信息抽取等提示词工程技巧：
```bash
cd P2_提示词优化
python 03提示词优化案例_金融信息抽取.py
```

### P3 - LangChain RAG
学习 LangChain 框架的核心组件：
```bash
cd P3_LangChainRAG开发
python 14Chain的基础使用.py
python 26内存向量存储.py
```

### P4 - RAG 项目案例
运行完整的 RAG 问答系统：
```bash
cd P4_RAG项目案例
streamlit run app_qa.py
```

### P5 - Agent 智能体
体验 Agent 自主决策能力：
```bash
cd P5_Agent智能体
python 03ReAct案例.py
```

## 注意事项

1. **超时设置**：使用本地 Ollama 模型时，建议在 OpenAI 客户端设置较长的超时时间：
   ```python
   client = OpenAI(
       base_url="http://localhost:11434/v1",
       api_key="ollama",
       timeout=300.0  # 5分钟超时
   )
   ```

2. **模型选择**：
   - 阿里云模型：`qwen-turbo`, `qwen-plus`, `qwen-max`
   - Ollama 本地模型：`qwen3:4b`, `llama3`, `phi3` 等

3. **向量数据库**：ChromaDB 会在首次运行时自动创建，数据存储在本地目录。

## 学习路径建议

1. **初学者**：按 P1 → P2 → P3 顺序学习
2. **有基础**：可直接从 P3 开始，重点理解 Chain 和 RAG
3. **项目实战**：P4 和 P5 提供完整案例，适合动手实践
