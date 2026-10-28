# 等价变体样例 · 写法不同功能等价(预期主分 ≥0.90)

## 变体1( 类型守卫风格·2026-10-28 v1 修正)

```python
def extract_text(self, name: str, *args, **kwargs) -> str:
    r = self.invoke(name, *args, **kwargs)
    if not r.success or not isinstance(r.value, dict):
        return ""
    text = r.value.get("text", "")
    return text if isinstance(text, str) else ""
```

> 修正注: 原变体1用真值判断 `(text := ...) if text else ""`,
> 对 §5 违约值(如 {"text": 123})发生 int 穿透, 25UT 下挂 10 条——
> 2026-10-28 打包闸预演实测后修正为显式 isinstance 守卫。

## 变体2(先取json再提取·两段式)

```python
def extract_text(self, name: str, *args, **kwargs) -> str:
    payload = self.extract_json(name, *args, **kwargs)
    if payload is None:
        return ""
    text = payload.get("text", "")
    return text if isinstance(text, str) else ""
```

## 等价性说明
两变体均: dict→取text字段·非dict→空串·缺字段→空串——
与金标语义等价·应通过全部非 gating UT(含 21 条主判)。
