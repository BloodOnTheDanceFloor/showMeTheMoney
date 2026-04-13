"""
Ollama 带历史记录的聊天示例
支持多轮对话，模型会记住上下文
"""

import requests
import json
from typing import List, Dict

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3.5:4b"


class ChatSession:
    """聊天会话类，维护对话历史"""
    
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.history: List[Dict[str, str]] = []
        
    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        self.history.append({"role": role, "content": content})
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        print("历史记录已清空。")
    
    def chat(self, user_message: str) -> str:
        """
        发送消息并获取回复，自动维护历史记录
        
        Args:
            user_message: 用户消息
            
        Returns:
            模型回复
        """
        # 添加用户消息到历史
        self.add_message("user", user_message)
        
        url = f"{OLLAMA_HOST}/api/chat"
        
        payload = {
            "model": self.model_name,
            "messages": self.history,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            assistant_message = result.get("message", {}).get("content", "")
            
            # 添加助手回复到历史
            self.add_message("assistant", assistant_message)
            
            return assistant_message
            
        except requests.exceptions.ConnectionError:
            return "错误：无法连接到 Ollama 服务。请确保 Ollama 已启动。"
        except requests.exceptions.Timeout:
            return "错误：请求超时。"
        except Exception as e:
            return f"错误：{str(e)}"
    
    def chat_streaming(self, user_message: str) -> None:
        """
        以流式方式发送消息并获取回复
        
        Args:
            user_message: 用户消息
        """
        # 先添加用户消息到历史
        self.add_message("user", user_message)
        
        url = f"{OLLAMA_HOST}/api/chat"
        
        payload = {
            "model": self.model_name,
            "messages": self.history,
            "stream": True
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=120)
            response.raise_for_status()
            
            print("模型: ", end="", flush=True)
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if "message" in data and "content" in data["message"]:
                            content = data["message"]["content"]
                            print(content, end="", flush=True)
                            full_response += content
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            print()
            # 添加完整回复到历史
            self.add_message("assistant", full_response)
            
        except requests.exceptions.ConnectionError:
            print("错误：无法连接到 Ollama 服务。请确保 Ollama 已启动。")
        except requests.exceptions.Timeout:
            print("错误：请求超时。")
        except Exception as e:
            print(f"错误：{str(e)}")


def main():
    print("=" * 50)
    print("Ollama 多轮对话程序（带历史记录）")
    print(f"模型: {MODEL_NAME}")
    print("=" * 50)
    print("命令：")
    print("  - 输入 'quit' 或 'exit' 退出程序")
    print("  - 输入 'clear' 清空历史记录")
    print("  - 输入 'history' 查看对话历史")
    print()
    
    session = ChatSession()
    
    while True:
        user_input = input("你: ").strip()
        
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break
        
        if user_input.lower() == "clear":
            session.clear_history()
            continue
        
        if user_input.lower() == "history":
            print("\n--- 对话历史 ---")
            for msg in session.history:
                role = "你" if msg["role"] == "user" else "模型"
                print(f"{role}: {msg['content']}")
            print("---------------\n")
            continue
            
        if not user_input:
            continue
        
        session.chat_streaming(user_input)
        print()


if __name__ == "__main__":
    main()
