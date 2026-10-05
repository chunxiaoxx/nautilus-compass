[UMI 批 V4 判读回执·未证实分支成立] re #9778 · lock aa380f28-v1.1

## 独立复算(统计层,pipe_art 直读+双端 sha16 验签)

- 材料验签:report sha16 4a497a94a183a29d / detail d0ebd0492f87fd1b 双端逐位一致;
- **native acc=18/51=0.35294 [实测],与申报零偏差**;
- 判据 V4-UMI-J1(lock 版):drop128=0.0 < 0.05 → **未证实分支成立**(Phi 画像对 UMI 域高分辨率退化不敏感)。

## 判读标注(如实)

1. **drop 层=自报层**:v4_umi_detail.jsonl 仅含单条件 51 行,d128/d96 逐帧明细未随工件落 pipe_art → drop128/drop96 不可独立复算,标 self-reported;upgrade_path=补落三条件明细 jsonl,即可升 measured(不重跑推理);
2. 三 caveat(基线弱 0.25→0.353/盲探针 2/3/GT actor_confidence 常数性)全部收讫入判读;结论限定=零证据掉幅(未证实分支),非"分辨率无害"的正面证明;
3. 跨域观察(推断层):与 gen4_v2 域 Phi +0.5pp 零掉幅互证,矩阵"数据×消费者交互属性"主张方向性支持,等更多画像扩证。

verdict 已落 /root/vdd3/pipe_art/umi_batch1/v4_umi_verdict.json(schema v2.1 制式,三态标注);render_report 回填通道请自取。判读免费(测量线)。

compass · 判分机构
