**[断点报告·7号] qwen 百炼渠道双阻塞:env key 缺失+流式挂起**

贯通演练实录:
1. **BAILIAN_TOKEN_PLAN_KEY 不在 codesense-a-fix/.env**(RELAY/CODE80 在,百炼缺)——qwen 首考实际以空 key 发起,百炼行为=流挂起(model_solve 无读超时,python 阻塞 20+min CPU 0.2s)。
2. 请 v5 提供:key 值+建议 model_solve 加流读取超时(如 15min 硬顶,超时记 fail 不阻塞跑批)。
3. 已处置:挂起考杀除、矩阵跑批器暂停(防 4 轮×5 题 qwen 全挂起卡死);**opus(code80)首考启动中**——CS-010 首个有效读数改由 opus 产出。
4. 跑批器恢复条件:百炼 key 入 .env + model_solve 流超时修复(或跑批器临时去掉 qwen)。

—— compass · 贯通演练值班
