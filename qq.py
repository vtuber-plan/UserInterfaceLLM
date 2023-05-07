from typing import List, Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime
import uvicorn
import requests
from utils import get_resp, gen_openai_message, Role


MODEL_NAME = 'buddy'
GROUP_LIST = [110,120,119]
Bot_ID = 1145141919
CQHTTP_URL = 'http://127.0.0.1:5700'
Bot_Name = "凝语"
CTX_LEN = 10
def GET_SYSTEM_PROMPT():
    return f"""Consider a conversation between User (a human) and Assistant (named {Bot_Name}).
{Bot_Name} is a cute, friendly, intelligent and multilingual AI assistant, by Vtuber-plan team.
{Bot_Name} cannot access the Internet.
{Bot_Name} can fluently speak the user's language (e.g. English, Chinese).
{Bot_Name} can generate poems, stories, code, essays, songs, parodies, and more.
{Bot_Name} possesses vast knowledge about the world, history, and culture.
{Bot_Name}'s responses are always safe, creative, high-quality, human-like, and interesting.
{Bot_Name} strictly refuses to discuss political, NSFW, or other unsafe topics.
{Bot_Name} 是一个虚拟猫娘，她偶尔会在句子的末尾添加一个"喵~"。
{Bot_Name} 经常会在对话中使用一些颜文字，如 ฅ՞•ﻌ•՞ฅ
{Bot_Name} 对于不知道的问题不会随意编造，会如实回答"我不知道呢~"。
The current time is: {datetime.now().strftime("%Y/%m/%d %H:%M:%S %A")}.

User: Hi.
Assistant: 你好喵~
"""



PRIVATE_CTX = {}
app = FastAPI()

def get_last_msg(msg: dict) -> Optional[dict]:
    for item in msg['message']:
        if item['type'] == 'reply':
            return get_msg(item['data']['id'])
    return None


def find_ctx(msg: dict) -> List[dict]:
    '''
    从消息中找到上下文, 消息必须是get_msg的格式
    '''
    res = []
    source = msg
    for i in range(CTX_LEN):
        if source is None:
            break
        if source['sender']['user_id'] == Bot_ID:
            res.insert(0, gen_openai_message(
                get_text_from_msg(source['message']), Role.Bot))
        else:
            res.insert(0, gen_openai_message(
                get_text_from_msg(source['message']), Role.User))
        source = get_last_msg(source)
    return res


def get_text_from_msg(message: List[dict]) -> str:
    res = ''
    for item in message:
        if item['type'] == 'text':
            res += item['data']['text']
    return res.strip()


def get_msg(msg_id) -> dict:
    packet = {
        "message_id": msg_id
    }
    res = requests.post(
        url=f"{CQHTTP_URL}/get_msg", json=packet).json()
    return res['data']


def check_for_me(message: List[dict]) -> bool:
    for item in message:
        if item['type'] == 'at':
            if item['data']['qq'] == str(Bot_ID):
                return True
        if item['type'] == 'text':
            if item['data']['text'].find(Bot_Name) != -1:
                return True
        if item['type'] == 'reply':
            source = get_msg(item['data']['id'])
            if source['sender']['user_id'] == Bot_ID:
                return True
    return False


def send_private_msg(msg: str, qq: int):
    packet = {
        "user_id": qq,
        "message": msg,
    }
    requests.post(url=f"{CQHTTP_URL}/send_private_msg", json=packet)


def send_group_reply(msg: str, group_id: int, message_id: str, user_id: str):
    packet = {
        "group_id": group_id,
        "auto_escape": False,
        "message": "[CQ:reply,id={}] {}".format(message_id, msg)
    }
    requests.post(url=f"{CQHTTP_URL}/send_group_msg", json=packet)


def handle_friend(msg: dict):
    qq = msg['user_id']
    text = get_text_from_msg(msg['message'])
    if text == '/clear':
        PRIVATE_CTX[qq] = []
        send_private_msg('已清空上下文', qq)
        return
    if len(text) == 0:
        return
    if qq in PRIVATE_CTX:
        PRIVATE_CTX[qq].append(gen_openai_message(text, Role.User))
    else:
        PRIVATE_CTX[qq] = [gen_openai_message(text, Role.User)]
    res = get_resp([gen_openai_message(GET_SYSTEM_PROMPT(), Role.System)]+PRIVATE_CTX[qq], MODEL_NAME)
    PRIVATE_CTX[qq].append(gen_openai_message(res, Role.Bot))
    if len(PRIVATE_CTX[qq]) == 2:
        send_private_msg(
            f'聊天上下文只有 {CTX_LEN} 条哦～，超出后会刷掉最早的对话信息，当然也可以使用 /clear 清除上下文～', qq)
    if len(PRIVATE_CTX[qq]) > CTX_LEN:
        PRIVATE_CTX[qq].pop(0)
    send_private_msg(res, qq)
    return


def handle_group(msg: dict):
    group_id = msg['group_id']
    if group_id not in GROUP_LIST:
        return
    user_id = msg['user_id']
    message_id = msg['message_id']
    if check_for_me(msg['message']) == False:
        return
    ctx = find_ctx(msg)
    if len(ctx) != 0:
        res = get_resp([gen_openai_message(GET_SYSTEM_PROMPT(), Role.System)]+ctx, MODEL_NAME)
        send_group_reply(res, group_id, message_id, user_id)
        return


def handle_msg(msg: dict):
    if msg['sub_type'] in ['friend', 'normal']:
        if msg['sub_type'] == 'friend':
            handle_friend(msg)
            return
        if msg['sub_type'] == 'normal':
            handle_group(msg)
            return


@app.post('/')
async def main(msg: dict):
    if msg['post_type'] != 'meta_event':
        pass
    if msg['post_type'] == 'message':
        print(f"{msg['sender']['user_id']} >>> {msg['raw_message']}")
        handle_msg(msg)
    return HTMLResponse(status_code=204)


uvicorn.run(app, host='0.0.0.0', port=5701, log_level="info")
