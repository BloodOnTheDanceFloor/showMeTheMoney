# Ollama 本地调用示例

本项目提供了通过 Python 程序调用本地 Ollama 服务的示例代码，使用 qwen3.5:4b 模型。

## 前提条件

1. 已安装并启动 Ollama 服务
2. 已下载 qwen3.5:4b 模型（或其他模型）

```bash
# 下载模型（如果还没有）
ollama pull qwen3.5:4b
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `chat_basic.py` | 基础单轮对话示例 |
| `chat_streaming.py` | 流式响应示例，实时显示生成内容 |
| `chat_with_history.py` | 多轮对话示例，支持上下文记忆 |

## 使用方法

### 1. 基础聊天

最简单的单轮对话，每次提问都是独立的：

```bash
python chat_basic.py
```

### 2. 流式聊天

实时显示模型生成的内容，体验更好：

```bash
python chat_streaming.py
```

### 3. 带历史记录的聊天

支持多轮对话，模型会记住上下文：

```bash
python chat_with_history.py
```

特殊命令：
- `clear` - 清空对话历史
- `history` - 查看对话历史
- `quit` / `exit` - 退出程序

## API 说明

### Ollama API 端点

- `POST /api/generate` - 单轮文本生成
- `POST /api/chat` - 多轮对话（带历史记录）

### 配置

默认配置：
```python
OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3.5:4b"
```

如需修改模型或其他参数，请编辑对应文件中的配置。

## 常见问题

1. **连接错误**：确保 Ollama 服务已启动
2. **模型不存在**：使用 `ollama list` 查看已安装的模型
3. **响应慢**：4B 模型在 CPU 上运行较慢，建议开启 GPU 加速
