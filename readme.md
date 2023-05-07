## User Interface

项目支持 OpenAI API 兼容接口

我们首要支持 FastChat 的这个 [Fork](https://github.com/jstzwj/FastChat)

**首次使用需要在对应 Python 文件中编辑全局变量**

### qq.py

通过 [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) http 和 反向 http 提供服务

### webui.py

依赖 streamlit

```shell
pip install streamlit
streamlit run webui.py
```