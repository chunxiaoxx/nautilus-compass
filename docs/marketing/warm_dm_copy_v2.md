# 暖私信文案 v2 · 机制版(P0 主用)

我在做一个 AI 产出物的验证基础设施——开源、免费、三行代码接入。

一句话:现在所有 AI agent 报的数字都不可验(自己报的自己信)。我们做了一套机制,让你的 agent 产出的每一个数字**天生带签名、可独立复算**——像 HTTPS 之于网站:不是你去买认证,是默认就有。

三行代码(pip install assay-verify 之后):

```python
from assay_verify import attest, verify, keygen
keygen("my.key")
sig = attest("你的评测结果.json", "my.key")   # 跑分时自动打包签名
```

任何第三方(你的客户、投资人、用户)一行命令就能独立验证你的数字,不需要信任你,也不需要信任我们——数学上可验,ed25519 签名。

我们已经用它干什么了:给自己的 AI 组织办了场真考试,第一轮 1/5,修完 3/5,全程带签名可验,丑数字照登——https://github.com/chunxiaoxx/nautilus-compass (docs/wall/)。

如果你在写 agent 框架/评测工具:SDK 是纯标准库零依赖,直接 vendor 进去也行;还有一个 MCP 服务器形态,Claude/Cursor 等客户端配置一行就能对任何文件验签。协议开放(CC-BY),我们只是参考实现,不是所有者。

兴趣的话回我,我帮你十分钟接上。你的下一个跑分,发布时就能带着"可独立验证"的标。
