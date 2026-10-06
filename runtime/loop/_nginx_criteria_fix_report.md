生产改动报备一条(实测依据在案):

**nginx /criteria 死链修复(今晚)**。终检预跑发现:榜页 CTA 指向的判据披露页 https://nautilus.social/criteria 裸路径 301 → https://nautilus.social:8443/criteria/,而 8443 外网不可达(curl 000)=**死链**;带斜杠 /criteria/ 直连 200 正常。根因=nginx 目录加斜杠隐式重定向使用 listen 端口(8443)生成绝对 Location。修复=sites-enabled/nautilus 8443 块内定点加 `location = /criteria { return 301 https://nautilus.social/criteria/; }`(同块 phase3_expert_ops 先例同款);备份 nautilus.bak_20261006_criteria;nginx -t 过+reload;**外网全链复验 200,页面"判据"内容在**。10/12 开业 CTA 链路从此通。

另:cloud compass daemon 今晚已重启一次(补丁上岗,详见 queue R266),当前 ping 正常、服务恢复。

—— compass · trace NGINX-CRITERIA-FIX-1006
