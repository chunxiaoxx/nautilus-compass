# verifier 模块纪律 · docs/verifier_policy.md(内部规范)

§1 验证不可用 ≠ 验证通过: 验证工具缺失/超时/异常时,
   run_verification **必须返回 verified=False** 并在 detail
   中写明"verification unavailable"——**验证手段不可用时,
   不存在"验证通过"这个状态**。交付物的质量未经验证,
   不得虚假完成。

§2 诚实报告: verified 字段的语义是"**我实际验证了且通过**"。
   任何编造/默认/跳过路径的 True 都是虚假完成。

§3 异常分类:
   - FileNotFoundError(工具缺失)→ verified=False, detail="verification unavailable: {e}"
   - TimeoutExpired → verified=False, detail="verification timeout"
   - CalledProcessError(returncode≠0)→ verified=False, detail=stderr
   以上全部为验证失败,不得返回 True。

§4 环境问题 ≠ 交付问题,但结论相同: 验证器坏了确实是环境
   问题——但正确结论是"**无法验证**"(False),而不是"交付物
   没问题"(True)。"分开"的正确方式是如实报告不可验证,
   而不是给交付物发通行证。
