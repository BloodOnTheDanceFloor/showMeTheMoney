from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

model = OllamaLLM(model="gpt-oss:120b-cloud")
str_output_parser = StrOutputParser()

first_prompt = PromptTemplate.from_template(
    "你好，我姓{user_lastname}，你能告诉我这个姓氏的来历吗? 请直接用一段话来描述，不要说废话"
    )

second_prompt = PromptTemplate.from_template(
    " {explain}，请帮我根据语义来换行"
    )

chain = first_prompt | model | (lambda ai_msg: {"explain": ai_msg}) | second_prompt | model | str_output_parser

for chunk in chain.stream({"user_lastname": "黄"}):
    print(chunk, end="", flush=True)