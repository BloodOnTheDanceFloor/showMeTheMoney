from openai import OpenAI
import json
import time

client = OpenAI(
    # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

schema = ['期数', '中奖号码', '一等奖']
examples_data = [
    {
        "content": "2025年第100期，开好红球22 21 06 01 03 11 篮球 07，一等奖中奖为2注。",
        "answers": {
            "期数": "2025100",
            "中奖号码": [1, 3, 6, 11, 21, 22, 7],
            "一等奖": "2注"
        }
    },
    {
        "content": "2025101期，有3注1等奖，10注2等奖，开号篮球11，中奖红球3、5、7、11、12、16。",
        "answers": {
            "期数": "2025101",
            "中奖号码": [3, 5, 7, 11, 12, 16, 11],
            "一等奖": "3注"
        }
    }
]

questions = [
    "2025年第102期，开奖红球05 08 12 19 23 28 篮球 09，一等奖中奖为5注。",
    "2025103期，有2注1等奖，8注2等奖，开号篮球06，中奖红球02、04、09、15、22、30。"
]


messages = [
    {"role": "system", "content": f"你帮我完成彩票信息抽取，我给你文本，你抽取{schema}信息，按JSON字符串输出。中奖号码需要包含6个红球和1个篮球，共7个数字，按升序排列红球，篮球放在最后。如果某些信息不存在，用'原文未提及'表示，请参考如下示例："}
]

for example in examples_data:
    messages.append(
        {"role": "user", "content": example["content"]}
    )
    messages.append(
        {"role": "assistant", "content": json.dumps(example["answers"], ensure_ascii=False)}
    )


for q in questions:
    start_time = time.time()

    response = client.chat.completions.create(
        model="qwen3:4b",
        messages=messages + [{"role": "user", "content": f"按照上述示例，现在抽取这个文本的信息：{q}"}]
    )

    elapsed_time = time.time() - start_time

    print(f"[用时: {elapsed_time:.2f}秒]")
    print(response.choices[0].message.content)
    print("-" * 50)
