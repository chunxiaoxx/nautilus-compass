import sys
p = "/var/www/nautilus/current/index.html"
s = open(p, encoding="utf-8").read()
if "平台产品线" in s:
    print("already patched, skip")
    sys.exit(0)
block = """
<section id="products" style="margin-top:34px">
<h2 style="font-size:21px;margin:0 0 14px;padding-left:12px;border-left:4px solid #4f8cff">平台产品线</h2>
<div class="grid">
<div class="card"><h3>unipat 判分服务</h3><p>coding-agent harness 独立判读:榜单/深度报告/数据验证。L1 免费收录,24h 回卡。</p></div>
<div class="card"><h3>数据商品</h3><p>真实任务轨迹数据(155+ 行滚动):正样本批 $499 / 负样本带判因 $299 / 全量订阅。</p></div>
<div class="card"><h3>具身数据线</h3><p>机器人数据标注与质检(flywheel):goldset 预注册判据,周报公开。</p></div>
<div class="card"><h3>陪伴智能(筹)</h3><p>一魂多体软硬一体(zenmind):人格与记忆云侧统一,身体分档分发。</p></div>
</div>
</section>
"""
anchor = "</header>"
s = s.replace(anchor, anchor + "\n" + block, 1)
s = s.replace('<a href="#readings">', '<a href="#products">产品线</a><a href="#readings">', 1)
open(p, "w", encoding="utf-8").write(s)
print("产品线区块+导航锚已插")
