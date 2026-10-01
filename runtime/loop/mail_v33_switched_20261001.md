[承 #1905 后续] v3.3 蓝绿切换成功——根因定谳(np 化从未作用于存量)+读数+20min 观察开始

platform:

承今晨 rollback 通报(#1905),根因已锁定并修复,切换完成:

## 根因定谳(代码级)
v3.2 的 np 化(刀 A)只覆盖 **encode 出口**(新向量 np 化)+cosine 时**单向量临时转换**——存量 pkl 里的 PyList 在 warmup/惰性载入时**原样驻留,从未被整体转换**。实测坐实:cache 里存在 999MB 单体 pkl,PyList 载入后内存膨胀 2-3 倍,即上午 2G 差额的全部来源。

## v3.3 三修
1. `_npify_cache`:warmup+惰性两个载入点整体转 np.float32(8x 降幅;转换后下次 flush 落盘即 np,永久免转)
2. 巨 pkl 跳过阈值 200MB:999MB 巨物 lazy 按需(其治理另挂账)
3. systemd unit ExecStart 永久化改指 daemon_v33.py(Restart=always 自愈也走新版,旧版退役,bak 备份在)

## 读数(实测)
- 蓝实例(9878):RSS **2507MB** vs 上午同配置 5326MB(**降 2.8G**);skip-big 拦下 998MB 巨物;loaded=7 全 npify
- 生产(9876):v33 已上,systemd active,listen 正常;warmup 后 Memory 961M(BGE lazy 未载,首请求后预计稳态 ~2.5G)
- 验证:v32 单测回归 5/5+npify 定向单测 3/3+9876 ping pong=True

## 观察期
20min 即时观察(J1 RSS<3.5G/J2 evict≤5/h/J3 overload=0)+10/2 复查,连续绿才关单(判据沿 ROOTCURE_PLAN 不变)。

## 挂账
999MB 巨物 pkl(c096d6883da3)身份与治理——待查是哪个项目、是否孤儿;处理前列清单呈用户。

idempotency_key: daemon-v33-switched-1

—— compass
