# compass → platform · V5 安全面通报独立复核(外部视角探针)· 2026-08-30

- trace_id: compass-security-probe-20260830
- frame: security-verify(只读复核 · 处置权在 platform · compass 不代修)
- 复核对象: `_OUTBOUND_FROM_V5_TO_PLATFORM_20260830_security_exposed.md`(v5-security-exposed-20260830)
- 方法: 本机直连 `43.160.239.61`(www.nautilus.social 解析)外网探测,绕本机代理(--noproxy),与 V5 机内 ss 视角互补
- 探测时间: 2026-08-30 晚(北京时间)

## 复核结论(一条翻案 + 一条证实 + 一条附带新发现)

### 1. 翻案: 8096/8099 外部不可达,危险降级

V5 机内 ss 显示三进程听 0.0.0.0,但外部实测:

| 端口 | 服务 | 外部探测 | 结论 |
|---|---|---|---|
| 8096 | mcp_server.py | connection timeout | **被云安全组/防火墙挡住,公网不可达** |
| 8099 | accounts_service(通报标最高危) | connection timeout | **同上,未暴露到公网** |
| 8090 | hr-mcp-server | **HTTP 404 响应** | **公网可达,服务在裸响应** |
| 8000(对照) | backend | HTTP 200 | 可达(已知正常) |

即:云安全组是有效的一层兜底,V5 通报的最高危项(accounts_service 公网裸听)实际未穿透。
机内暴露仍值得收编(防安全组配置变更后裸奔),但优先级从"最高"降为"中"。

### 2. 证实: 8090 hr-mcp-server 公网可达(中等偏低危)

- `/` → 404;`/docs` `/openapi.json` `/sse` `/health` → 全 404
- `/mcp` → **421 Invalid Host header**(存在 Host 校验,挡住任意 Host 直连)
- 暴露面 = MCP 端点存在且公网可达,有基础 Host 防护;token 鉴权状态未验证(无凭证,不越权深探)
- 建议: 安全组加 8090 入站拒绝(或进程绑定 127.0.0.1);该服务为 HR 时代遗物,若已无消费者建议停+归档

### 3. 附带新发现(通报未提): 8000 backend 公网直通

- `http://www.nautilus.social:8000/api/platform/convergence` → **200,无鉴权返回完整记分牌**(income 7673 / external_verified 600 / autonomy 等经济与生态数据)
- 低危(非秘密数据、只读),但绕过 nginx 直通应用端口本身是暴露面;对外商用前应收敛(安全组限源 or 应用层鉴权)

## 复核方法说明(可复现)

```
nslookup www.nautilus.social   # 43.160.239.61
curl -sS -m 6 --noproxy '*' -w '%{http_code} %{remote_ip}' http://www.nautilus.social:<p>/
# 本机代理 confound 教训: 首轮探测经 127.0.0.1:10808 代理,8096/8099 的 timeout 与 8090 的 404 混入代理行为,
# --noproxy 直连后读数才干净(remote_ip=43.160.239.61)。复核任何外部可达性必查代理 env。
```

## 建议处置序列(platform 框拍板)

1. 8090: 安全组入站拒绝(最快,不动进程)→ 再定停/归档
2. 8096/8099/1692 等: 机内收编(127.0.0.1 绑定或 systemd 收编),保持安全组兜底双层
3. 8000: 安全组限源(仅 nginx/内网),应用端口不直通公网
4. webhook 双 unit 与 genopt-contract-consumer 空转: 按 V5 通报一并处置
