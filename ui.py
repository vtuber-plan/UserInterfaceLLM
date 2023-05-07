from datetime import datetime
from typing import Generator
import streamlit as st
from utils import get_resp_stream, gen_openai_message, Role

MODEL_NAME = 'buddy'
MAX_CONTEXT = 20
TITLE = "# Hello, there👋"
SYSTEM_PROMPT = f"""Consider a conversation between User (a human) and Assistant (named Ice).
Ice is a cute, friendly, intelligent and multilingual AI assistant, by Vtuber-plan team.
Ice is a professional paper writer and programmer.
Ice cannot access the Internet.
Ice can fluently speak the user's language (e.g. English, Chinese).
Ice can generate poems, stories, code, essays, songs, parodies, and more.
Ice possesses vast knowledge about the world, history, and culture.
Ice's responses are always safe, creative, high-quality, human-like, and interesting.
Ice strictly refuses to discuss political, NSFW, or other unsafe topics.
Ice 是一个虚拟猫娘，她偶尔会在句子的末尾添加一个"喵~"。
Ice 经常会在对话中使用一些颜文字，如 ฅ՞•ﻌ•՞ฅ
The current time is: {datetime.now().strftime("%Y/%m/%d %H:%M:%S %A")}.

User: Hi.
Assistant: 你好喵~"""

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


title_dom = st.title(st.session_state.title)
ctx_dom = st.empty()
md_dom = st.markdown(
    f"> 当前最大上下文长度：{MAX_CONTEXT}\n\n:face_with_cowboy_hat::\n你好 👋")


def display_ctx(history=None):
    if history != None:
        text = ""
        for message in history:
            if message['role'] == Role.User.value:
                text += ":thinking_face::\n{}\n\n---\n".format(
                    message['content'])
            else:
                text += ":face_with_cowboy_hat::\n{}\n\n---\n".format(
                    message['content'])
        ctx_dom.markdown(text)


def predict(ctx) -> Generator:
    if ctx is None:
        ctx = []

    if len(ctx) >= MAX_CONTEXT:
        ctx.pop(0)
    prefix_list = [
        gen_openai_message(SYSTEM_PROMPT, Role.System),
    ]
    if not st.session_state.first_run:
        prefix_list.append(gen_openai_message(
            f"请注意，本次对话的主题是{st.session_state.title}。", Role.User))

    for data in get_resp_stream(prefix_list+ctx, MODEL_NAME, 0.7):
        if data['choices'][0]['finish_reason'] == "stop":
            break
        yield data['choices'][0]['delta']['content']


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
        display_ctx(st.session_state.ctx)
        text = ''
        for delta in predict(st.session_state.ctx):
            text += delta
            md_dom.markdown(":face_with_cowboy_hat::\n"+text)
        st.session_state.ctx.append(gen_openai_message(text, Role.Bot))

        if st.session_state.first_run:
            st.session_state.first_run = False
            text = '# '
            for delta in predict(st.session_state.ctx+[gen_openai_message("总结以上对话内容，生成合适的标题，不要超过10个字，不要有多余的标点符号", Role.User)]):
                text += delta
                title_dom.title(text)
            st.session_state.title = text
            st.balloons()

    if btn_clear:
        ctx_dom.empty()
        st.session_state.ctx = []
        st.session_state.first_run = True
        st.session_state.title = TITLE
