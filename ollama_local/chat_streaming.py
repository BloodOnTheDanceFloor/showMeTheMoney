"""
Ollama 流式响应聊天示例
实时显示模型生成的内容，体验更好
"""

import requests
import json

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3.5:4b"


def chat_streaming(prompt: str) -> None:
    """
    以流式方式发送消息给 Ollama 模型，实时显示回复
    
    Args:
        prompt: 用户输入的提示词
    """
    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        response.raise_for_status()
        
        print("模型: ", end="", flush=True)
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if "response" in data:
                        print(data["response"], end="", flush=True)
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
        
        print()  # 最后换行
        
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到 Ollama 服务。请确保 Ollama 已启动。")
    except requests.exceptions.Timeout:
        print("错误：请求超时。")
    except Exception as e:
        print(f"错误：{str(e)}")


def main():
    print("=" * 50)
    print("Ollama 流式聊天程序")
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
        
        chat_streaming(user_input)
        print()


if __name__ == "__main__":
    main()
