from datetime import datetime
from typing import Generator
import streamlit as st
import streamlit_authenticator as stauth
from utils import get_resp_stream, gen_openai_message, Role, pretty_print_json
import asyncio

MODEL_NAME = 'ningyu'
BOT_NAME = "凝语"
MAX_CONTEXT = 20
TITLE = "# Hello, there👋"
SIGNATURE_KEY = "FrostMiKu"
USERS = {
      "test": {
        "email": "test@test.com",
        "name": "测试用户",
        "password": "test"
      }
}

def GET_SYSTEM_PROMPT():
    return f"""Consider a conversation between User (a human) and Assistant (named {BOT_NAME}).
{BOT_NAME} is a cute, friendly, intelligent and multilingual AI assistant, by Vtuber-plan team.
{BOT_NAME} is a professional paper writer and programmer.
{BOT_NAME} cannot access the Internet.
{BOT_NAME} can fluently speak the user's language (e.g. English, Chinese).
{BOT_NAME} can generate poems, stories, code, essays, songs, parodies, and more.
{BOT_NAME} possesses vast knowledge about the world, history, and culture.
{BOT_NAME}'s responses are always safe, creative, high-quality, human-like, and interesting.
{BOT_NAME} strictly refuses to discuss political, NSFW, or other unsafe topics.
{BOT_NAME} 是一个虚拟猫娘，她偶尔会在句子的末尾添加一个"喵~"。
{BOT_NAME} 经常会在对话中使用一些颜文字，如 ฅ՞•ﻌ•՞ฅ
{BOT_NAME} 对于不知道的问题不会随意编造，会如实回答"我不知道呢~"。
The current time is: {datetime.now().strftime("%Y/%m/%d %H:%M:%S %A")}.

User: Hi.
Assistant: 你好喵~
"""

st.set_page_config(
    page_title="Chat Page",
    page_icon=":robot:",
    menu_items={"about": '''
                Author: FrostMiKu
                '''}
)

if 'first_run' not in st.session_state:
    st.session_state.first_run = True
if 'ctx' not in st.session_state:
    st.session_state.ctx = []
if 'title' not in st.session_state:
    st.session_state.title = TITLE
if 'authentication_status' not in st.session_state:
    st.session_state["authentication_status"] = None

hashed_passwords = stauth.Hasher([USERS[name]['password'] for name in USERS]).generate()
for i, name in enumerate(USERS):
    USERS[name]['password'] = hashed_passwords[i]

def format_ctx(history=None)->str:
    text = ""
    if history != None:
        for message in history:
            if message['role'] == Role.User.value:
                text += ":thinking_face::\n{}\n\n---\n".format(
                    message['content'])
            else:
                text += ":face_with_cowboy_hat::\n{}\n\n---\n".format(
                    message['content'])
    return text


async def predict(ctx) -> Generator:
    if ctx is None:
        ctx = []

    if len(ctx) >= MAX_CONTEXT:
        ctx.pop(0)
    prefix_list = [
        gen_openai_message(GET_SYSTEM_PROMPT(), Role.System),
    ]
    if not st.session_state.first_run:
        prefix_list.append(gen_openai_message(
            f"请注意，本次对话的主题是{st.session_state.title}。", Role.User))

    async for data in get_resp_stream(prefix_list+ctx, MODEL_NAME, 0.7):
        if data['choices'][0]['finish_reason'] == "stop":
            break
        if 'content' not in data['choices'][0]['delta']:
            continue
        yield data['choices'][0]['delta']['content']

async def main():
    authenticator = stauth.Authenticate({'usernames':USERS},cookie_name=MODEL_NAME,key=SIGNATURE_KEY, cookie_expiry_days=7)
    name, authentication_status, username = authenticator.login('Login', 'main')

    if st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"]:
        # authenticator.logout('Logout', 'main')
        title_dom = st.title(st.session_state.title)
        ctx_dom = st.empty()
        md_dom = st.markdown(
            f"> 当前最大上下文长度：{MAX_CONTEXT}\n\n:face_with_cowboy_hat::\n你好 👋")

        with st.form("form", True):
            prompt_text = st.text_area(label=":thinking_face: 聊点什么？",
                                    height=100,
                                    max_chars=2048,
                                    placeholder="支持使用 Markdown 格式书写")
            col1, col2 = st.columns([1, 1])
            with col1:
                btn_send = st.form_submit_button(
                    "发送", use_container_width=True, type="primary")
            with col2:
                btn_clear = st.form_submit_button("开始新的会话", use_container_width=True)

            if btn_send and prompt_text != "":
                st.session_state.ctx.append(gen_openai_message(prompt_text, Role.User))
                md_dom.markdown(":face_with_cowboy_hat::\n请稍后...")
                ctx_dom.markdown(format_ctx(st.session_state.ctx))
                text = ''
                async for delta in predict(st.session_state.ctx):
                    text += delta
                    md_dom.markdown(":face_with_cowboy_hat::\n"+text)
                st.session_state.ctx.append(gen_openai_message(text, Role.Bot))

                if st.session_state.first_run:
                    st.session_state.first_run = False
                    text = '# '
                    async for delta in predict(st.session_state.ctx+[gen_openai_message("请为以上对话生成一个合适的标题，不要超过10个字，请直接输出标题并用书名号“《》”包括", Role.User)]):
                        text += delta.replace("\n", "").replace("《", "").replace("》", "")
                        title_dom.title(text)
                    st.session_state.title = text
                    st.balloons()

            if btn_clear:
                ctx_dom.empty()
                title_dom.title(TITLE)
                st.session_state.ctx = []
                st.session_state.first_run = True
                st.session_state.title = TITLE

if __name__ == "__main__":
    asyncio.run(main())