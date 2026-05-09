# Compass · Compliance Notices

> Status: 2026-05-05 · for legal review · v1.0 GA target
> Replace template legal language before public deployment.

## CCPA Notice (California Consumer Privacy Act · 加州消费者隐私法)

### Categories of personal information collected

When you use Compass, we collect:

| Category | Specific data | Source |
|---|---|---|
| Identifiers | email · user_id · agent_id · device_id | You provide on signup |
| Internet activity | timestamps · agent_type · region · IP (transient) | Auto-collected |
| Inferences | drift score · type/concept distribution | Derived from your observations |
| Content | name · description · body of observations | You provide via API/MCP |

### Encrypted-at-rest data we cannot read

For Pro+ users, observation content (name · description · body) is
end-to-end encrypted on your client. We physically cannot read this
content. We only see metadata (timestamp · type · drift label · region).

### Sale of personal information

**We do not sell your personal information.** We do not derive ad
identifiers, behavioral profiles, or any product that we sell to
third parties.

### Right to know

You can retrieve your data anytime:

- All observations: `GET /v1/observations`
- Profile aggregate: `GET /v1/profile`
- Audit log (90d): `GET /v1/audit_log`

### Right to delete

`DELETE /v1/users/me` triggers:
1. Observations table: delete all rows where user_id = you
2. Agents table: delete all your agents
3. Audit log: hard-delete after 30-day retention
4. Cross-region replicas: cascading delete in 7 days

### Right to opt out

There is no opt-out — we don't sell your data to begin with.

### Contact

chunxiaoxx@gmail.com

---

## GDPR Notice (EU General Data Protection Regulation)

### Lawful basis

We process your personal data based on:
- **Contract** (Article 6.1.b) — to provide the service you signed up for
- **Legitimate interest** (Article 6.1.f) — for security and abuse prevention
- **Consent** (Article 6.1.a) — for optional features (cross-region sync, marketplace)

### Data Controller

```
Nautilus Platform
[ADDRESS · TBD before EU launch]
DPO: chunxiaoxx@gmail.com
```

### Data Processor (when self-hosted)

When you self-host (`docker-compose up`), you are the data controller
and we are not involved in your data processing.

### Data subject rights (Articles 15-21)

| Right | Article | How |
|---|---|---|
| Access | 15 | `GET /v1/observations` etc. |
| Rectification | 16 | Edit/re-write observations |
| Erasure | 17 | `DELETE /v1/users/me` |
| Restriction | 18 | Pause processing: contact chunxiaoxx@gmail.com |
| Portability | 20 | Export endpoint (planned v0.9.5) |
| Object | 21 | Cancel account |

### Retention

| Data | Retention |
|---|---|
| Active observations | Until you delete |
| Profile aggregate | Updated lazily; deleted with account |
| Audit log | 90 days from event |
| Backups | 30 days then encrypted destruction |
| Soft-deleted account data | 30 days then hard-delete |

### Data transfers outside EU

For EU-region users: data stays in `eu-frankfurt` (AWS Frankfurt).
We do not transfer to non-EU regions unless you explicitly opt in
via `POST /v1/auth/export-region`.

### Breach notification

If we become aware of a personal data breach affecting you,
we will notify you within 72 hours per Article 33-34.

### DPA (Data Processing Agreement)

For enterprise / business deployments:
[email chunxiaoxx@gmail.com for DPA template before signing service contract]

---

## PIPL Notice (China · 个人信息保护法)

### 个人信息处理者 (Personal Information Processor)

```
Nautilus Platform
[地址 · TBD]
个人信息保护负责人 (DPO): chunxiaoxx@gmail.com
```

### 收集的个人信息类型

| 类型 | 具体内容 | 来源 |
|---|---|---|
| 身份标识 | 邮箱 · user_id · agent_id | 用户注册 |
| 行为信息 | timestamps · agent_type · 区域 · IP (短暂) | 自动收集 |
| 衍生信息 | drift 分数 · 类型/概念分布 | 系统推导 |
| 内容信息 | 观察名称 · 描述 · 正文 | 用户通过 API/MCP 提交 |

Pro+ 用户的内容信息为客户端 E2EE 加密 · 服务器无法解密。

### 处理目的

- 提供 cross-agent memory recall 服务 (主要)
- 提供 drift detection 警示功能 (主要)
- 安全监控和滥用防止 (基于合法利益)
- 改进产品 (基于聚合匿名数据 · 你可以拒绝)

### 数据出境

中国大陆用户的数据存储在 **cn-shanghai** 区域 (腾讯云 / 阿里云上海机房)。
数据 **默认不出境**。如需跨境传输 (例如用户从中国搬到欧洲)，必须经由
`POST /v1/auth/export-region` endpoint 显式申请，并可能需要按
《数据出境安全评估办法》申报。

### 你的权利

- 知情权: `GET /v1/observations` 等查询
- 决定权: 可以拒绝功能 · 可以删除账户
- 查阅复制权: 上述 endpoint
- 更正权: 重新写观察来更正
- 删除权: `DELETE /v1/users/me` (30天软删 · 然后硬删)
- 解释权: 你可以要求我们解释自动决策 (drift 评分等)

### 备案 / 许可

- ICP 备案号: [TBD · 部署到大陆前必须申请]
- 数据出境申报: 仅在用户主动请求时

### 投诉 / 联系

```
邮箱: chunxiaoxx@gmail.com
监管投诉: 国家互联网信息办公室
```

---

## Common (all jurisdictions)

### What we don't do

- ❌ Sell user data to advertisers
- ❌ Use user observations to train general models
- ❌ Read encrypted observation content (technically impossible at Pro+)
- ❌ Share data with governments without legal process
- ❌ Auto-enable cross-region sync without explicit consent

### What we do

- ✅ Encrypt at rest (Pro+) and in transit (TLS 1.3)
- ✅ Maintain audit logs you can review
- ✅ Honor delete requests within 30 days
- ✅ Notify you of breaches within 72 hours
- ✅ Open-source the entire codebase so you can verify

### Self-host

If you self-host, you are the data controller. None of the above
notices apply to compass.nautilus.social vs you. Use SELF_HOST.md
guide and write your own privacy policy for your end users.

---

## Updates to this notice

Last updated: 2026-05-05.

We will email you 30 days before any material change.
Minor changes (typo · clarification) we just push to git.

Subscribe to the changelog: GitHub Watch · CHANGELOG.md
