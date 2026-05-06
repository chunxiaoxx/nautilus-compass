# compass v1.0 · Region sharding architecture

> Status: design · 2026-05-05 · 实施 v0.9.5 (cn-shanghai 第一个) · v1.0 全 3 region
> 目标: 数据本地化 (PIPL · GDPR · CCPA 合规) · 默认不跨境 · 用户授权才能 export

## 三个 region

```
┌─────────────────────────────────────────────────────────────┐
│  cn-shanghai     (Tencent / Aliyun 上海机房)                  │
│  · 中国大陆 user                                              │
│  · PIPL 合规 · 数据不出境                                      │
│  · 模型: Volc Ark coding plan (DeepSeek/MiniMax/GLM/Kimi/...)│
├─────────────────────────────────────────────────────────────┤
│  eu-frankfurt    (AWS Frankfurt / Hetzner)                   │
│  · 欧盟 user                                                 │
│  · GDPR 合规 · right-to-be-forgotten · DPA                   │
│  · 模型: Anthropic Claude · Mistral · OpenAI EU              │
├─────────────────────────────────────────────────────────────┤
│  us-virginia     (AWS US East-1)                             │
│  · 北美 user (default for English locale)                    │
│  · CCPA 合规                                                 │
│  · 模型: Anthropic / OpenAI · Gemini · 全部商用             │
└─────────────────────────────────────────────────────────────┘
```

## 路由规则 (nginx + JWT.region claim)

```nginx
# nginx.conf · upstream by JWT region claim

map $jwt_region $upstream_region {
    cn-shanghai   compass-cn;
    eu-frankfurt  compass-eu;
    us-virginia   compass-us;
    default       compass-cn;          # 国内 fallback (大陆部署)
}

upstream compass-cn { server cn-1.compass:8000; server cn-2.compass:8000; }
upstream compass-eu { server eu-1.compass:8000; server eu-2.compass:8000; }
upstream compass-us { server us-1.compass:8000; server us-2.compass:8000; }

server {
    listen 443 ssl http2;
    server_name compass.nautilus.social;

    ssl_certificate     /etc/letsencrypt/live/compass.nautilus.social/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/compass.nautilus.social/privkey.pem;

    # 解析 JWT 的 region claim (用 lua-resty-jwt)
    access_by_lua_block {
        local jwt = require "resty.jwt"
        local auth = ngx.var.http_authorization or ""
        if auth:sub(1, 7) == "Bearer " then
            local token = auth:sub(8)
            local jwt_obj = jwt:verify(ngx.var.jwt_secret, token)
            if jwt_obj.verified and jwt_obj.payload.region then
                ngx.var.jwt_region = jwt_obj.payload.region
            end
        end
    }

    # 路由到对应 region
    location / {
        proxy_pass http://$upstream_region;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Region $jwt_region;
    }
}
```

## DNS 策略

```
compass.nautilus.social         → CDN (Cloudflare) · WAF + DDoS
                                → Anycast 路由到最近 region

cn.compass.nautilus.social      → cn-shanghai 直连 (国内 user)
eu.compass.nautilus.social      → eu-frankfurt 直连
us.compass.nautilus.social      → us-virginia 直连

# 不通过 CDN 的硬路径 (合规要求 / 调试用)
```

## sqlite (per region)

```
cn-1: /var/lib/compass/cn/compass.db
cn-2: /var/lib/compass/cn/compass.db   (replica · async)

eu-1: /var/lib/compass/eu/compass.db
us-1: /var/lib/compass/us/compass.db

# v1.0 用 LiteFS / Turso 做 multi-region replication
# v0.9.5 阶段单 region · sqlite 落地即可
```

## bge-m3 daemon (per region)

```
每 region 独立部署 daemon (60-90s 冷启动)
  · cn-1 + cn-2: 各 1 个 T4 GPU 实例 · 共享存储 (但模型独立)
  · eu-1: AWS g4dn.xlarge (T4)
  · us-1: AWS g4dn.xlarge

模型权重镜像:
  · cn: hf-mirror.com (国内加速)
  · eu/us: huggingface.co 直连
```

## 跨 region 同步 (默认 OFF)

```
默认: 每 region 独立 · 数据不跨境

用户主动授权 export:
  POST /v1/auth/export-region
    body: {target_region: "eu-frankfurt", user_passphrase}
  
  服务器:
    1. 从 source region 取 user 全部 obs (encrypted)
    2. 用 user passphrase 重新派生 master key (key 不上传)
    3. client 重新加密所有 obs · 上传到 target region
    4. 30d 后 delete source region 数据 (用户可 cancel)

→ 数据出境只在用户明确请求时 · 类似 1Password 的 region migration
```

## 合规 checklist

```
PIPL (China · 个人信息保护法):
  ✓ 数据不出境 (默认)
  ✓ 用户授权出境时 · 走 cross-border data transfer 申报流程
  ✓ Right to delete (硬删 + 30d 留痕)
  ✓ 数据脱敏 (server 端只索引 metadata · 不解密内容)
  ✓ 中国本地服务器 (Tencent / Aliyun 上海机房 · 备案)

GDPR (EU):
  ✓ Privacy by design (E2EE 默认)
  ✓ Right to be forgotten
  ✓ Data portability (export endpoint)
  ✓ DPA (Data Processing Agreement) for enterprise
  ✓ EU 服务器 (Frankfurt) · 不跨境

CCPA (California):
  ✓ Opt-out of data sale (我们不卖)
  ✓ Right to know what's collected
  ✓ Right to delete
```

## 实施时间表

```
v0.9.0  · 单 region (cn-shanghai 起步) · 部署在 compass.nautilus.social
v0.9.2  · auth + JWT region claim · 但只 1 region 在线
v0.9.5  · cn-1 + cn-2 (HA + sqlite replica)
v0.9.6  · eu-frankfurt 上线 · GDPR DPA template
v1.0    · us-virginia 上线 · 三 region 全
v1.0.1  · 跨 region export endpoint (用户授权)
```

## 成本估算

```
cn-shanghai (Tencent · 1 个 T4 spot + 2 个 sqlite VM):
  · GPU: ¥300/月 (T4 spot)
  · VM: ¥100/月 (2 × small)
  · CDN: ¥50/月 (流量低)
  · 总: ¥450/月 (~$65)

eu/us 类似但 USD 计:
  · GPU: $130/月
  · VM: $50/月
  · CDN: $20/月
  · 总: $200/月 each region

3 region 总 cost: ~$465/月 = 可承受 (融资 seed 预算覆盖)
```
