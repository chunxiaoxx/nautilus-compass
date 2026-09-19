# assay-verify

**AI 产出物的验证 SDK** — Let's Encrypt 模式,不是穆迪模式。验证不是一项服务,
是默认。Assay Protocol v0 的参考实现(CC-BY,任何人可实现)。

## 三行代码

```python
from assay_verify import verify, attest, keygen

keygen("my.key")                                # 一次性:生成密钥对
sig = attest("claims.json", "my.key")           # 生产端:产出即打包(自动签名)
result = verify("claims.json", sig, pub_hex)    # 消费端:一行验真
```

自定义声明(基准数字、agent 产出):

```python
payload = {"agent": "my-bot", "benchmark": "swe-x", "score": 0.83,
           "sha256": hashlib.sha256(artifacts).hexdigest()}
sig = attest("run.log", "my.key", payload=payload)
```

## 三态语义(诚实验证器必须能说"算不了")

- `VALID` — 签名有效且哈希吻合
- `INVALID` — 验签失败(篡改或错钥)
- `MALFORMED` — 材料缺失/格式错

## 特性

- **零第三方依赖**,纯标准库(python ≥3.8)
- ed25519(RFC 8032)纯 python 实现,与 nautilus-compass 主实现**交叉互验**通过
- 向后兼容:直接验证 compass 已发布的签名成绩单(docs/wall/)

## 安装(即将上 PyPI)

```bash
pip install assay-verify
```

或直接拷贝 `assay_verify/` 目录(单包,无依赖,欢迎 vendor)。
