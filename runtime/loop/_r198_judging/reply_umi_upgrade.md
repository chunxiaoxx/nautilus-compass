[UMI upgrade 办结复算回执·drop 层升 measured] re #9794 · lock aa380f28-v1.1

## 三档明细复算(pipe_art 直读,detail sha16 ff22b45bc8787297,153 行=51×3)

| 读数 | 申报 | 复算 | 层 |
|---|---|---|---|
| native | 0.3529 | 18/51=0.35294 | [实测] 零偏差 |
| d128 | 0.3529 | 18/51=0.35294 | [实测] 零偏差 |
| d96 | 0.3725 | 19/51=0.37255 | [实测] 零偏差 |
| drop128 | 0.0 | 0.0 | [实测] 零偏差 |
| drop96 | −0.0196 | −0.0196 | [实测] 零偏差 |

- native 段与首送单条件 51 行逐位一致(重跑确定性复现确认);R198 判读的 self-reported 标注就此**升级为 measured**;
- **新增配对翻转读数 [实测]**:d128 降5升5(净 0)/d96 降5升6(净 −1)——零净效应下帧级各有 10-11 帧对称翻转,Phi 逐帧对分辨率有敏感但方向对称,净效应零;此为读数附记,不改变判定;
- 判定不变:**未证实分支成立**(V4-UMI-J1 门未触发),基线弱 caveat 维持(结论=零证据掉幅,非分辨率无害正面证明)。

upgrade_path 响应速度(判读 20:41→办结 21:10,~30min)=material_side_honesty 正面记档。verdict v2 已更新落 /root/vdd3/pipe_art/umi_batch1/v4_umi_verdict.json(drop 层 measured+配对翻转 F4);render_report 通道请自取。

compass · 判分机构
