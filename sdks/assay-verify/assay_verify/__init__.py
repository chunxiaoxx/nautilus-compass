# -*- coding: utf-8 -*-
"""assay-verify · AI 产出物的验证 SDK(Let's Encrypt 模式,Assay Protocol v0)。

三行代码::

    from assay_verify import verify, attest, keygen

    keygen("my.key")                                   # 一次性
    sig = attest("claims.json", "my.key")              # 生产端:产出即打包
    result = verify("claims.json", sig, pub_hex)       # 消费端:一行验真(三态)

零第三方依赖,纯标准库。协议:Assay Protocol v0(CC-BY)。
"""
from ._core import verify, attest, keygen, AssayResult  # noqa: F401

__version__ = "0.1.0"
__all__ = ["verify", "attest", "keygen", "AssayResult"]
