# 笔记本 → Mac mini · Claude Code + 会话历史迁移筹备(2026-10-16 · R544)

> 传输通道:**NAS 中转**(大型文件)+ 内网直传(小而敏感)。NAS 同时成为组织文件中枢(全网持续接入)。

## 一、迁移体量盘点 [实测]

| 类别 | 体量 | 迁移方式 |
|---|---|---|
| **会话历史**(全项目 jsonl) | **3.0GB**(~1520 项目目录,大头:flywheel 1.2G/arm-worker-prime 861M/compass 235M) | **NAS 打包中转** |
| **记忆库**(memory/,热层语义资产) | ~50MB(1520 项目中含 memory 的子集;compass 9MB/v5 7MB 等) | **NAS 打包**(与历史分包) |
| Claude Code 配置(settings/hooks/agents/skills/plugins) | plugins 1.3G(含 BGE 旧模型缓存,可瘦身)+ skills 8.9M | plugins **瘦身后** NAS(去掉 .cache 大文件);其余内网直传 |
| **凭据缓存**(~/.claude/.cache 各 key env) | 34M(含 pkl) | ⚠️ **不经 NAS 明文**——内网 scp 直传或用户手动 |
| MCP 配置(.claude.json) | 小 | 内网直传(**路径审计后**:Windows 路径→macOS) |
| 衍生缓存(daemon pkl 嵌入向量) | 不迁——Mac mini MPS 批量重建(分钟级) | — |
| 工作仓库(nautilus-compass/v5/core...) | git clone 即可(Mac mini 有 GitHub 认证后) | git 自拉 |

## 二、NAS 中转结构(建议)

```
<nas-root>/nautilus-migration/
├── 01_sessions/          # 会话历史(3GB,按项目分 tar)
│   ├── sessions_compass.tar.zst
│   ├── sessions_flywheel.tar.zst
│   └── ...
├── 02_memory/            # 记忆库热层(~50MB)
│   └── memory_all.tar.zst
├── 03_claude_config/     # 配置(瘦身后)
│   └── claude_config.tar.zst
└── README_MANIFEST.json  # 每包 sha256+文件清单(校验用)
```

NAS 上传后,Mac mini 侧 `rsync -av --checksum` 拉取(校验传输完整性),解压到对应路径。

## 三、打包脚本(Windows 侧,我执行)

`tools/migrate_pack_to_nas.py`:
1. 会话历史:每项目 tar.zst(分卷避免单包过大);
2. memory_all:全部项目 memory/ 目录(排除 .tmp);
3. claude_config:settings.json+hooks+agents+skills(plugins 只收 manifest 级,剔除大缓存);
4. **manifest**:逐包 sha256+计数;
5. 输出 `~/nas-outbox/` 待传目录。

## 四、敏感项处理(纪律)

- **各 API key env 文件不经 NAS**——迁移日由 compass 经**局域网 ssh 直传**到 Mac mini `.claude/.cache/`(或用户手动),全程内网不出;
- `.claude.json` 内含 MCP token——同上直传+路径审计;
- NAS 若非可信内网(有公网映射),凭据类永不落 NAS。

## 五、Mac mini 侧落地(包到位后)

1. Claude Code 安装:`npm i -g @anthropic-ai/claude-code`(或 brew);
2. 解压 sessions→`~/.claude/projects/`;memory→同;config→`~/.claude/`;
3. `.claude.json` 路径审计(C:\Users\chunx→/Users/chunx;C:/→/);
4. **daemon 迁移**:仓根 daemon.py+daemon_start.sh(路径审计)+Mac mini 侧嵌入指向本地 8400(本机 BGE,**不再需要远程嵌入**——Mac mini 自己就是嵌入宿主!);
5. hook 注册:settings.json 的 SessionStart/UserPromptSubmit 指向 macOS 路径;
6. 验收:claude 启动→hook 注入→recall 命中→出卡查询→判读工作台。

## 六、NAS 需要用户提供

1. NAS 访问方式(IP/协议 SMB/NFS/WebDAV/SSH)+ 凭据(或已挂载盘符);
2. 可用容量 ≥10GB;
3. (可选)是否希望 NAS 上常驻“组织文件中枢”结构(以后所有大件走 NAS)。

—— compass · R544 · 打包脚本今日内出,待 NAS 信息即上传
