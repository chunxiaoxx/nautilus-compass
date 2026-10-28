# 钥匙台账(KEY LEDGER · 平台维护 · M1 起用)

> 每行=一把已注册凭证。私钥永不入此账(只有公钥指纹)。吊销在"状态"列记日期+原因。
> 格式:`agent | 类型 | 指纹(sha256前16) | 挂载仓 | 权限 | 状态 | 登记日期`

| agent | 类型 | 指纹 | 挂载仓 | 权限 | 状态 | 登记日 |
|---|---|---|---|---|---|---|
| v5 | DeployKey(ED25519)+SSH签名二合一 | SHA256:osOPgRhxpNg…(996b56dee0f9ddb4) | chunxiaoxx/nautilus-v5 | write | ✅已注册(id 165254567,回读验) | 2026-10-03 |
| v5 | 同上(第二把,shared 用) | 待生成 | Nautilus-agent/shared | write | ⏳org 禁 deploy key 策略待用户开(组织设置→Deploy keys) | 2026-10-03 |
| (批次一 prime 钥匙待其回执,死线 10/5) | | | | | | |
| chunxiaoxx-personal | PAT(classic 全scope) | n/a(用户自持) | 全部 | admin | 用户持有,agent 禁例行使用(M1 判据5) | 2026-10-03 |
| prime-001 | DeployKey(ED25519) | SHA256:gxWdTYrgjvrl…(gxWdTYrgjvrlpmdVNu0GlTfqLxCu5jg9BaAFlH3JhTM) | Nautilus-agent/prime | write | ✅注册(id 165317994)+ssh -T 实测认证据;私钥暂存 cloud:/home/ubuntu/agent-keys/prime-001/(600),待框领取 | 2026-10-04 |
| soul | DeployKey(ED25519) | SHA256:PdM0qesYuikJ…(PdM0qesYuikJAW1Y2jUBc+aOkmeCdXMTmfLXEJ8iMCs) | Nautilus-agent/soul | write | ✅注册(id 165317984)+ssh -T 实测认证;私钥暂存 cloud:/home/ubuntu/agent-keys/soul/(600),待框领取 | 2026-10-04 |
| kairos | DeployKey(ED25519) | SHA256:BG5XXEkVWNBn…(BG5XXEkVWNBn7fGp+HduMTYA/WxAO91DNQ2+c63lqJM) | Nautilus-agent/kairos | write | ✅注册(id 165317995)+ssh -T 实测认证;私钥暂存 cloud:/home/ubuntu/agent-keys/kairos/(600),待框领取 | 2026-10-04 |
| v7 | DeployKey(ED25519) | SHA256:V1zXVVCE58Ei…(V1zXVVCE58EimW+zuWZX4PO9OvtKnkyWcP9Fdg/+hoU) | Nautilus-agent/v7 | write | ✅注册(id 165317996)+ssh -T 实测认证;私钥暂存 cloud:/home/ubuntu/agent-keys/v7/(600),待框领取 | 2026-10-04 |
| flywheel | DeployKey(ED25519) | SHA256:m7D6lCMWLX7N…(m7D6lCMWLX7NVs/vKN5Pr1vez7SfyvcVsNI+QirbXUc) | Nautilus-agent/flywheel | write | ✅已领取+首验(回执#2907:首推 7245cd9 GitHub 在档核验);私钥已迁移框侧 | 2026-10-04 |
| compass | DeployKey(ED25519) | SHA256:BR85VX8XkjNa…(BR85VX8XkjNakhvzZeyL9/IrLnvK7bifv6utmiOe9yA) | Nautilus-agent/compass | write | ✅已领取+首验(回执#2904:首推 9272a0f GitHub 在档核验);私钥已迁移框侧 | 2026-10-04 |
