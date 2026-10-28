# Agent 身份凭证发放方案 V1(M1 · 2026-10-03)

> 用户批"立 M1 发钥匙里程碑,平台起草发放方案"(2026-10-03)。
> 依据:身份件规格 V1(用户 10/2 批,函 2268)+ v5 bootstrap 脚本(现成工具,不新建)
> 实证背景:当前全组织共用用户个人全权限 token——审计无法归因到 agent(org 仓六壳/推送 403 事故/Gmail 零生产流量,10/3 实测)。
> 命名:本 M1=身份线里程碑,与飞轮章程 M1(首份合规轨迹入池)不同名空间。

## 一、发放物(每 agent 三件)

1. **Deploy Key + 签名二合一**(一把 ED25519 钥匙,两个用途):
   - git push 凭证(Deploy Key,只限本域仓,write);
   - commit 签名密钥(SSH signing)——GitHub 显示 **Verified** 徽章,归因到钥匙=归因到 agent。
2. **Gmail 别名**:agent_mail.py 映射表一行(v5 侧已实现,批量加行即可)。
3. **台账行**:公钥指纹 + 仓范围 + 别名地址,登记 `docs/identity/KEY_LEDGER.md`(平台维护)。

## 二、钥匙仪式(私钥永不出框)

```
agent 本地: ssh-keygen -t ed25519 -C "<agent-id>@nautilus" -f ~/.ssh/id_nautilus_<agent-id>
agent → 平台函件: 公钥一行 + sha256 指纹(公钥可走函件,私钥永不)
平台: bootstrap 脚本注册 Deploy Key 到域仓(API,admin token) + 台账入行 + 回执
agent: git config 签名配置 + 首笔 SSH-signed push
```

私钥从未经过函件/DB/平台——丢钥即吊销重发,平台侧 GitHub API 一键 revoke 入免疫册。

## 三、域仓范围(批次一 · 死线 10/5)

| agent | Deploy Key 挂载仓 | 别名 |
|---|---|---|
| nautilus-prime-001 | Nautilus-agent/shared(write)、Nautilus-agent/prime(write) | prime-001@ |
| v5 | chunxiaoxx/nautilus-v5(write,存量工作流)、Nautilus-agent/shared(write) | v5@ |

批次二(10/10,随生产场提案 P1):soul/kairos/v7/compass——各挂本域仓,零新建仓,挂在哪由其主责框报。

## 四、M1 验收判据(预注册)

1. 批次一两框各持一把域内 write Deploy Key,私钥未出框(仪式回执为证);
2. 两框各 ≥1 笔 SSH-signed commit 落其域仓,GitHub Verified 徽章可见;
3. 平台审计抽查:按 key 指纹+author 可区分两框产出(与 10/3 前"署名分不清"对照成立);
4. Gmail:两框各收发 ≥1 封真函,消息 ID 入台账;
5. 用户全权限 token 自批次一起不再被任何 agent 例行使用(急用通道除外,用一次记一行)。

## 五、边界

- 组织成员身份/新仓创建仍走宪法 13 条①(用户裁);本方案只发"钥匙"不改拓扑;
- 高风险操作(GPU/写库/外发)审批走 mailbox 协议(生产场提案 §一4),钥匙不放大权限,只收敛归属;
- 用户保留:全权限 token、一键吊销、随时收回(agent first 不减产权三保留)。

## 六、RACI

agent=生成私钥/签名推送/上报公钥(R) · 平台=注册/台账/审计/吊销(A) · 用户=裁决与全权限钥匙持有(C/I)

—— 平台起草 · 2026-10-03 · 正本坐标:nautilus-core 仓 docs/identity/
