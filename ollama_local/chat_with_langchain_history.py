# 长期会话记忆 - Ollama 本地模型版本（使用 LangChain）
# 本文件演示如何使用 LangChain 的 ChatOllama 实现带历史记录的对话功能

# 导入操作系统模块，用于文件和目录操作
import os
# 导入 JSON 模块，用于消息的序列化和反序列化
import json
# 导入类型提示，用于指定函数参数和返回值的类型
from typing import Sequence

# 从 langchain_ollama 导入 Ollama 聊天模型类
# OllamaLLM 是 LangChain 提供的用于与 Ollama 本地模型交互的类
from langchain_ollama import OllamaLLM
# 从 langchain_core.messages 导入消息相关的工具函数和基类
# message_to_dict: 将消息对象转换为字典格式，便于存储
# messages_from_dict: 将字典列表转换回消息对象列表
# BaseMessage: 所有消息类型的基类
from langchain_core.messages import message_to_dict, messages_from_dict, BaseMessage
# 从 langchain_core.chat_history 导入聊天历史基类
# BaseChatMessageHistory: 定义了聊天历史管理的接口规范
from langchain_core.chat_history import BaseChatMessageHistory
# 从 langchain_core.output_parsers 导入字符串输出解析器
# StrOutputParser: 将模型输出解析为字符串
from langchain_core.output_parsers import StrOutputParser
# 从 langchain_core.prompts 导入提示词模板相关类
# ChatPromptTemplate: 用于构建聊天格式的提示词模板
# MessagesPlaceholder: 用于在模板中占位历史消息
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# 从 langchain_core.runnables 导入带历史记录的 Runnable 包装器
# RunnableWithMessageHistory: 为链添加自动管理历史消息的功能
from langchain_core.runnables import RunnableWithMessageHistory


# ========================================
# 自定义文件存储的聊天历史类
# ========================================

class FileChatMessageHistory(BaseChatMessageHistory):
    """
    基于文件存储的聊天历史类
    继承自 BaseChatMessageHistory，实现将对话历史持久化到本地文件
    """

    def __init__(self, session_id: str, storage_path: str):
        """
        初始化文件聊天历史对象

        参数:
            session_id: 会话的唯一标识符，用于区分不同用户的对话
            storage_path: 存储文件的目录路径
        """
        # 保存会话ID，用于标识不同的对话会话
        self.session_id = session_id
        # 保存存储路径，指定历史文件存放的文件夹
        self.storage_path = storage_path
        # 组合完整的文件路径：目录 + 会话ID作为文件名
        self.file_path = os.path.join(self.storage_path, self.session_id)

        # 确保存储目录存在，如果不存在则自动创建
        # exist_ok=True 表示如果目录已存在不会报错
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """
        添加新消息到历史记录

        参数:
            messages: 要添加的消息序列（列表或元组）
        """
        # 获取当前已有的所有消息，转换为列表
        # self.messages 是一个 property，会自动调用 messages() 方法
        all_messages = list(self.messages)
        # 将新消息扩展到已有消息列表中
        all_messages.extend(messages)

        # 将消息对象列表转换为字典列表，便于 JSON 序列化
        # 使用列表推导式遍历所有消息，将每个消息转为字典
        new_messages = [message_to_dict(message) for message in all_messages]

        # 以写入模式打开文件，使用 UTF-8 编码
        # 使用 json.dump 将字典列表写入文件
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(new_messages, f, ensure_ascii=False, indent=2)

    @property
    def messages(self) -> list[BaseMessage]:
        """
        获取所有历史消息

        返回:
            消息对象列表，如果文件不存在则返回空列表
        """
        # 尝试从文件读取历史消息
        try:
            # 以读取模式打开文件
            with open(self.file_path, "r", encoding="utf-8") as f:
                # 从 JSON 文件加载数据，得到字典列表
                messages_data = json.load(f)
                # 使用 messages_from_dict 将字典列表转换回消息对象列表
                return messages_from_dict(messages_data)
        # 如果文件不存在（首次对话），返回空列表
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        """
        清空所有历史消息
        将空列表写入文件，相当于删除所有历史
        """
        # 以写入模式打开文件，写入空列表
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)


# ========================================
# 模型和链的配置
# ========================================

# 创建 Ollama 本地聊天模型实例
# ChatOllama 是专门为聊天场景设计的 Ollama 模型封装
# model: 指定要使用的 Ollama 模型名称，需要提前通过 ollama pull 下载
# base_url: Ollama 服务的地址，默认为 http://localhost:11434
model = OllamaLLM(model="gpt-oss:120b-cloud")

# 创建聊天格式的提示词模板
# 使用 from_messages 方法定义多轮对话的格式
prompt = ChatPromptTemplate.from_messages(
    [
        # 系统消息：定义 AI 的角色和行为
        ("system", "你是一个 helpful 的 AI 助手，需要根据会话历史回应用户问题。"),
        # MessagesPlaceholder: 占位符，用于插入历史消息
        # 这里的 "chat_history" 是变量名，对应传入的历史消息列表
        MessagesPlaceholder("chat_history"),
        # 人类消息：用户输入的模板
        # {input} 是占位符，会被实际的用户输入替换
        ("human", "{input}")
    ]
)

# 创建字符串输出解析器
# 用于将模型的输出解析为纯字符串
str_parser = StrOutputParser()


# ========================================
# 辅助函数和链的组装
# ========================================

def print_prompt(full_prompt):
    """
    打印提示词的调试函数
    用于查看实际发送给模型的完整提示词内容
    """
    # 打印分隔线和提示词内容
    print("=" * 50)
    print("【实际发送的提示词】")
    print(full_prompt.to_string())
    print("=" * 50)
    # 返回提示词，继续链的执行
    return full_prompt


# 组装基础链（Chain）
# 使用管道符 | 连接各个组件，形成处理流水线
# 流程: 提示词模板 -> 打印调试 -> 模型调用 -> 输出解析
base_chain = prompt | print_prompt | model | str_parser


def get_history(session_id: str) -> FileChatMessageHistory:
    """
    获取指定会话的历史记录对象

    参数:
        session_id: 会话ID

    返回:
        FileChatMessageHistory 对象
    """
    # 创建并返回文件历史记录对象
    # 历史文件存储在 ./chat_history 目录下
    return FileChatMessageHistory(session_id, "./chat_history")


# 创建带历史记录功能的对话链
# RunnableWithMessageHistory 会自动管理历史消息的添加和检索
conversation_chain = RunnableWithMessageHistory(
    base_chain,                         # 基础链，被增强的原始链
    get_history,                        # 获取历史记录的函数
    input_messages_key="input",         # 用户输入在模板中的变量名
    history_messages_key="chat_history" # 历史消息在模板中的变量名
)


# ========================================
# 主程序入口
# ========================================

if __name__ == '__main__':
    # 配置当前会话的 session_id
    # 相同 session_id 的对话会共享历史记录
    session_config = {
        "configurable": {
            "session_id": "user_001"  # 可以改为不同的ID来创建新会话
        }
    }

    # 示例 1：第一次对话，建立上下文
    print("\n【第一次对话】")
    res = conversation_chain.invoke(
        {"input": "小明有22个猫"},
        session_config
    )
    print("AI 回复:", res)

    # 示例 2：第二次对话，继续上下文
    print("\n【第二次对话】")
    res = conversation_chain.invoke(
        {"input": "小刚有11只狗"},
        session_config
    )
    print("AI 回复:", res)

    # 示例 3：基于历史上下文提问
    print("\n【第三次对话 - 基于历史提问】")
    res = conversation_chain.invoke(
        {"input": "总共有几个宠物"},
        session_config
    )
    print("AI 回复:", res)

    # 示例 4：新会话（没有历史记录）
    print("\n【新会话 - 无历史记录】")
    new_session_config = {
        "configurable": {
            "session_id": "user_002"  # 不同的 session_id
        }
    }
    res = conversation_chain.invoke(
        {"input": "总共有几个宠物"},
        new_session_config
    )
    print("AI 回复:", res)
