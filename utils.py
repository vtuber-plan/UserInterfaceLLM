from enum import Enum
import requests
import json
from typing import Generator, List

BASE_URL = 'http://127.0.0.1:8000'

def get_resp_stream(ctx: List[dict], model:str, temperature:float=0.7) -> Generator:
    packet = {
        "model": model,
        "messages": ctx,
        "temperature": temperature,
        "stream": True,
    }
    res = requests.post(
        url=f'{BASE_URL}/v1/chat/completions', json=packet, stream=True)
    if res.status_code != 200:
        raise Exception(res)
    for chunk in res.iter_lines():
        data = chunk.decode()[6:]
        if len(data) == 0 or data[-1] != '}':
            continue
        yield json.loads(data)


def get_resp(ctx: List[dict], model:str, temperature:float=0.7) -> str:
    packet = {
        "model": model,
        "messages": ctx,
        "temperature": temperature,
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

def pretty_print_json(json_string:str):
    json_obj = json.loads(json_string)
    print(json.dumps(json_obj, indent=4, sort_keys=True))

if __name__ == '__main__':
    import httpx
    from httpx_sse import connect_sse
    mock_ctx = [{"role": "system", "content": "你是一个名为Ice的人工智能助手"},{"role": "user", "content": "你好啊"}]
    packet = {
        "stream": True,
        "model": 'buddy',
        "messages": mock_ctx,
        "temperature": 0.7,
    }
    with httpx.Client() as client:
        with connect_sse(client, "POST", f'{BASE_URL}/v1/chat/completions',json=packet) as event_source:
            for sse in event_source.iter_sse():
                print(sse.event, sse.data, sse.id, sse.retry)

