"""
Ollama 基础聊天示例
使用 qwen3.5:4b 模型进行简单的单轮对话
"""

import requests
import json

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3.5:4b"


def chat_once(prompt: str) -> str:
    """
    发送单条消息给 Ollama 模型并获取回复
    
    Args:
        prompt: 用户输入的提示词
        
    Returns:
        模型的回复文本
    """
    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
        
    except requests.exceptions.ConnectionError:
        return "错误：无法连接到 Ollama 服务。请确保 Ollama 已启动。"
    except requests.exceptions.Timeout:
        return "错误：请求超时。模型可能需要更长时间来生成回复。"
    except Exception as e:
        return f"错误：{str(e)}"


def main():
    print("=" * 50)
    print("Ollama 本地聊天程序")
    print(f"模型: {MODEL_NAME}")
    print("=" * 50)
    print("提示：输入 'quit' 或 'exit' 退出程序")
    print()
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break
            
        if not user_input:
            continue
        
        print("\n模型思考中...")
        response = chat_once(user_input)
        print(f"模型: {response}\n")


if __name__ == "__main__":
    main()
