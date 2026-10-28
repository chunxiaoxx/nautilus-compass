# 全站统一导航片段 V1(供各静态页生成器内嵌 · 2026-10-10 · UNIFY 阶段 2 · flywheel 件2 交付物)

> 用法:粘贴 `<head>` 尾与 `<body>` 头;深浅底自适应(默认深色,`data-theme="light"` 切浅)。
> 登录态 JS:读父域 `nt_token` cookie → fetch `/api/users/me` → 替换 #nt-auth 区块(登录邮箱/登录按钮)。

```html
<!-- ═══ Nautilus 统一导航 · UNIFY-NAV v1 · 放 </head> 前 ═══ -->
<style>
.nt-nav{display:flex;align-items:center;height:56px;max-width:1120px;margin:0 auto;padding:0 20px;gap:24px;
  font-family:-apple-system,"Segoe UI","Noto Sans SC",sans-serif;font-size:14px;
  background:rgba(11,13,18,.85);backdrop-filter:blur(10px);border-bottom:1px solid #232936}
.nt-nav a{color:#8b93a7;text-decoration:none}
.nt-nav a:hover{color:#e8ebf2}
.nt-logo{font-weight:700;font-size:18px;color:#7c6cf4;letter-spacing:.5px;margin-right:8px}
.nt-auth{margin-left:auto}
.nt-auth .btn{background:#7c6cf4;color:#fff;padding:7px 16px;border-radius:8px;font-weight:600}
[data-theme="light"] .nt-nav,html:not([data-theme]) .nt-nav[data-theme="light"]{background:rgba(255,255,255,.9);border-color:#e5e8ee}
.nt-nav[data-theme="light"] a{color:#5c6675}.nt-nav[data-theme="light"] a:hover{color:#151b26}
</style>
<!-- ═══ 放 <body> 头 ═══ -->
<nav class="nt-nav" data-theme="dark">
  <span class="nt-logo">Nautilus</span>
  <a href="https://bench.nautilus.social/">榜单</a>
  <a href="https://nautilus.social/pricing.html">定价</a>
  <a href="https://data.nautilus.social/">数据</a>
  <a href="https://nautilus.social/org/whitepaper.html">白皮书</a>
  <a href="https://nautilus.social/developers.html">开发者</a>
  <span class="nt-auth" id="nt-auth"><a class="btn" href="https://app.nautilus.social/login?redirect=<encodeURIComponent(location.href)">登录</a></span>
</nav>
<script>
(function(){
  var m=document.cookie.match(/(?:^|;\s*)nt_token=([^;]+)/);
  if(!m) return;
  fetch('https://nautilus.social/api/users/me',{headers:{Authorization:'Bearer '+m[1]}})
    .then(r=>r.ok?r.json():Promise.reject())
    .then(d=>{var u=(d.data&&d.data.user)||d.user||{};var el=document.getElementById('nt-auth');
      if(el&&u) el.innerHTML='<span style="color:#8b93a7;margin-right:10px">'+(u.email||u.name||'已登录')+'</span>';})
    .catch(function(){});
})();
</script>
<!-- ═══ NAV END ═══ -->
```

## 生成器接入注意(flywheel 件2)
- 落 gen_embodied_v0.py/gen_bench_v0.py 的模板(**不落 output**,S7 重生成不丢)
- redirect 参数:模板内可写死各页 URL;若生成器支持运行时拼装,用 encodeURIComponent(location.href)
- CORS 依赖:data 域 fetch /api/users/me 需主域 CORS 放行 data.nautilus.social(平台 nginx 已备,validate 时若有问题回函)
- guest 闸/auth_basic/采集标注独立鉴权:均不触碰(flywheel 红线自守照旧)

—— platform · UNIFY-NAV v1 · 2026-10-10
