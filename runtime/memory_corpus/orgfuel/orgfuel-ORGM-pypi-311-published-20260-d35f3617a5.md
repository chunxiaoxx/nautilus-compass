---
name: orgfuel-ORGM-pypi-311-published-20260-d35f3617a5
description: "--- name: pypi-311-published-20260906 description: PyPI 3.1."
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-pypi-311-published-20260
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: pypi-311-published-20260906
description: PyPI 3.1.1 发布定案(9/6)——三重独立验证绿·构建配方 --no-isolation·403=截断 token 教训·README 补 pip Quickstart
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-08T14:24:02.492Z
---

PyPI `nautilus-compass 3.1.1` 2026-09-06 发布定案:

**验证(三重,非自报)**:①pypi.org/project/nautilus-compass/3.1.1/ → 200;②JSON API latest=3.1.1;③`pip download --index-url https://pypi.org/simple/ nautilus-compass==3.1.1` 真实拉下 wheel。

**发布前事实纠偏**:包早已存在到 3.0.1(作者 chunxiaoxx,自家非抢注)——README L22 的 PyPI badge 一直是活的,3.1.1 上去后 latest 自动指新。

**配方**:
- 构建:Store Python 的 `python -m build` 隔离 venv 有 bug(executable missing)→ 用 **`python -m build --no-isolation`**(当前环境需 setuptools+wheel)。
- 上传:`TWINE_USERNAME=__token__ TWINE_PASSWOR
