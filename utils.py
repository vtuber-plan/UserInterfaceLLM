from enum import Enum
import httpx
import requests
import json
from typing import Generator, List

BASE_URL = 'http://127.0.0.1:8000'

async def get_resp_stream(ctx: List[dict], model:str, temperature:float=0.7, top_p:float=0.9) -> Generator:
    packet = {
        "model": model,
        "messages": ctx,
        "max_tokens": 2048,
        "temperature": temperature,
        "top_p": top_p,
        "stream": True,
    }
    # res = requests.post(
    #     url=f'{BASE_URL}/v1/chat/completions', json=packet, stream=True)
    async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{BASE_URL}/v1/chat/completions",
                json=packet,
                timeout=20,
            ) as response:
                async for chunk in response.aiter_text():
                    if not chunk:
                        continue
                    for line in chunk.split("\n\n"):
                        if not line:
                            continue
                        if line.startswith("data: "):
                            line = line.removeprefix("data: ")
                        if line.strip() == "[DONE]":
                            break
                        yield json.loads(line)
    # if res.status_code != 200:
    #     raise Exception(res)
    # for chunk in res.iter_lines():
    #     data = chunk.decode()[6:]
    #     if len(data) == 0 or data[-1] != '}':
    #         continue
    #     yield json.loads(data)


def get_resp(ctx: List[dict], model:str, temperature:float=0.7, top_p:float=0.9) -> str:
    packet = {
        "model": model,
        "messages": ctx,
        "max_tokens": 2048,
        "temperature": temperature,
        "top_p": top_p,
    }
    res = requests.post(
        url=f'{BASE_URL}/v1/chat/completions', json=packet)
    if res.status_code != 200:
        print(res)
        return "喵喵喵~出错了！"
    return res.json()['choices'][0]['message']['content']


class Role(Enum):
    User = 'user'
    Bot = 'assistant'
    System = 'system'


def gen_openai_message(content: str, role: Role) -> dict:
    return {
        "role": role.value,
        "content": content
    }

def pretty_print_json(data:str|dict):
    if isinstance(data, str):
        data = json.loads(data)
    print(json.dumps(data, indent=4, sort_keys=True))

if __name__ == '__main__':
    mock_ctx = [{"role": "system", "content": "你是一个名为Ice的人工智能助手"},{"role": "user", "content": "你好啊"}]
    packet = {
        "stream": True,
        "model": 'buddy',
        "messages": mock_ctx,
        "temperature": 0.7,
    }

