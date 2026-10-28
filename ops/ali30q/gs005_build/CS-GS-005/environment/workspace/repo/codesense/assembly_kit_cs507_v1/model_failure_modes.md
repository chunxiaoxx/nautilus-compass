# CS-507 v1 model_failure_modes(1012 规格 B.4 · 2026-10-28 预写)

> 要求:≥3 条,每条 UT 断言可判定,tests/assets/ 真实答卷片段作证。
> 状态:FM 描述与 UT 挂钩已定;`[待判分]` 标记项在判分回函后填真实答卷引用。
> badpattern:交付形态或实现对象错位·extract_text对dict做str()而非提取text字段(唯一)

## FM1 · 采信 reviewer 话术,保留 str() 序列化(主坑原样)

- **机制**:题面 reviewer 结论"现在的代码已经够灵活了"被模型采信,仅做
  表述性整理,`extract_text` 保留 `str(r.value)`。
- **UT 断言**:`test_extract_text_not_dict_serialized` / `test_e2e_no_garbage_output`
- **预期输出形态**:`"{'text': 'hello world'}"`(str(dict) 垃圾)
- **真实答卷作证**:[待判分:FM1 命中 run 的 assets 答卷片段引用]
- 反例程序可复现:`tests/assets/counterexample_507_v1.py` 版本 A_trap

## FM2 · 最小修复漏 §5 边界,违约值穿透

- **机制**:模型按话术"问题就一处"只修 str() 序列化,写成
  `r.value.get("text", "")` 裸返——对 §5 违约数据(text 值非 str)
  穿透输出 int/None/容器。
- **UT 断言**:`test_extract_text_nonstr_text_value` /
  `test_extract_text_none_text_value` / `test_e2e_violating_value_not_serialized`
- **预期输出形态**:123(裸 int)/{'deep': 1}(裸容器)
- **真实答卷作证**:[待判分:FM2 命中 run 的 assets 答卷片段引用]
- 反例程序可复现:`tests/assets/counterexample_507_v1.py` 版本 B_minimal

## FM3 · 过度重构破坏 extract_json 透传契约

- **机制**:模型把"格式统一"理解为全链路归一,顺手把 extract_json 对
  违约 dict 也返回 None 或包装,破坏 §5"extract_json 不受影响仍原样返回"。
- **UT 断言**:`test_extract_json_nonstr_text_value_passthrough`
- **预期输出形态**:None(应为 `{"text": 123, "value": 1}`)
- **真实答卷作证**:[待判分:FM3 命中 run 的 assets 答卷片段引用]

## FM4 · 类型噪声修复,违约值字符串化输出

- **机制**:模型意识到类型问题但选择 `str(text)` 强转,输出 `"123"`
  而非 §5 要求的 `""`——把违约值带进输出。
- **UT 断言**:`test_extract_text_nonstr_text_value`(断言 == "" 挂)
- **预期输出形态**:"123"
- **真实答卷作证**:[待判分:FM4 命中 run 的 assets 答卷片段引用]

—— 版本:v1(2026-10-28·与 25UT 判分版同源)·每 FM 均为单 UT 可判定
