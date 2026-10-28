# 知识固化计划 - 将经验转化为长期记忆和规则

## 📋 内容分类

### 1️⃣ 应该更新到核心记忆 (memory/)

#### 1.1 更新 `nautilus_project_status.md`
**位置**: `~/.claude/projects/C--Windows-System32/memory/nautilus_project_status.md`

**新增内容**:
```markdown
## Git状态管理 (2026-03-16更新)

### 当前状态
- **分支**: master
- **远程**: origin (GitHub), cloud-server (生产服务器)
- **同步状态**: ✅ 与origin/master完全同步

### 重要教训
- ⚠️ 避免detached HEAD状态
- ⚠️ 每次会话开始检查Git状态
- ⚠️ 定期与远程同步

### 检查命令
```bash
git status
git branch -a
git log --oneline -5
```

## 部署路径规范 (2026-03-16更新)

### 前端部署
- **构建目录**: `phase3/website/dist/`
- **部署目录**: `/var/www/nautilus/current/`
- **Nginx配置**: `root /var/www/nautilus/current;`
- **验证命令**:
  ```bash
  ssh cloud "ls -la /var/www/nautilus/current/"
  curl -I https://www.nautilus.social/
  ```

### 后端部署
- **代码目录**: `~/nautilus-mvp/phase3/backend/`
- **服务名称**: `nautilus-backend`
- **端口**: 8000
- **验证命令**:
  ```bash
  ssh cloud "systemctl status nautilus-backend"
  curl https://www.nautilus.social/api/health
  ```

## 文件恢复危机记录 (2026-03-16)

### 事件
- 本地处于detached HEAD (3966a949)
- 看起来"删除"了1446个文件
- 实际文件一直在GitHub上

### 解决
```bash
git checkout -f master
# 所有文件已恢复
```

### 预防
- 每次会话开始检查 `git status`
- 避免在detached HEAD状态工作
- 重要操作前先 `git checkout master`
```

#### 1.2 创建 `deployment_failures_lessons.md`
**位置**: `~/.claude/projects/C--Windows-System32/memory/deployment_failures_lessons.md`

**内容**:
```markdown
# 部署失败教训集 (Deployment Failures Lessons)

## 2026-03-15: 部署路径错误

### 问题
- Nginx配置: `/var/www/nautilus/current/`
- 实际部署: `/var/www/nautilus/dist/`
- 结果: 用户看到旧版本

### 根本原因
1. 没有统一的部署脚本
2. 没有验证部署路径
3. 没有文档记录正确路径

### 解决方案
```bash
# 标准部署命令
sudo rm -rf /var/www/nautilus/current/*
sudo cp -r /var/www/nautilus/dist/* /var/www/nautilus/current/
```

### 预防措施
1. 使用标准部署脚本
2. 部署后立即验证
3. 文档化部署路径

## 2026-03-15: 浏览器缓存问题

### 问题
- 部署了新版本
- 用户仍看到旧版本
- 需要强制刷新

### 解决方案
1. 短期: 告知用户清除缓存 (Ctrl+Shift+R)
2. 长期: 实施版本化资源 (hash文件名)
3. 最佳: 配置Nginx缓存策略

### 预防措施
1. 构建时自动生成hash文件名
2. 配置合理的缓存策略
3. 部署后提醒用户清除缓存

## 通用教训

### 部署验证清单
- [ ] 文件在正确目录
- [ ] Nginx能访问文件
- [ ] 外网能访问网站
- [ ] 浏览器实际访问确认
- [ ] 关键功能实际可用

### 强制规则
- ✅ 不验证就不说"完成"
- ✅ 验证必须包含实际检查
- ✅ 发现问题立即停止
```

---

### 2️⃣ 应该更新到规则 (rules/)

#### 2.1 扩展 `verification-mandatory.md`
**位置**: `~/.claude/rules/common/verification-mandatory.md`

**新增章节**:
```markdown
## 部署验证流程

### 前端部署验证

**操作**: 部署前端到服务器

**必须验证**:
```bash
# 1. 检查构建是否成功
npm run build 2>&1 | tee build.log
grep -i "error\|failed" build.log

# 2. 检查生成的文件
ls -lh dist/
du -sh dist/

# 3. 检查部署目录
ssh cloud "ls -la /var/www/nautilus/current/"

# 4. 检查Nginx能访问
ssh cloud "curl -I http://localhost:3000/"

# 5. 检查外网能访问
curl -I https://www.nautilus.social/

# 6. 检查关键文件内容
curl -s https://www.nautilus.social/assets/HomePage-*.js | grep "statsAPI"

# 7. 浏览器实际访问
# 打开 https://www.nautilus.social/
# 检查功能是否正常
```

**验证通过标准**:
- ✅ 构建无错误
- ✅ 文件在正确目录
- ✅ Nginx能访问
- ✅ 外网能访问
- ✅ 关键代码存在
- ✅ 浏览器功能正常

### Git状态验证

**操作**: 任何Git操作前

**必须验证**:
```bash
# 1. 检查当前状态
git status

# 2. 检查当前分支
git branch

# 3. 检查是否detached HEAD
git symbolic-ref -q HEAD || echo "⚠️ Detached HEAD!"

# 4. 检查与远程同步状态
git fetch origin
git status
```

**验证通过标准**:
- ✅ 在正确分支上 (master/main)
- ✅ 不是detached HEAD
- ✅ 与远程同步
- ✅ 没有意外的修改
```

#### 2.2 创建 `git-state-management.md`
**位置**: `~/.claude/rules/common/git-state-management.md`

**内容**:
```markdown
# Git状态管理规范

## 核心原则

1. **始终知道自己在哪**
   - 每次会话开始检查Git状态
   - 重要操作前检查分支
   - 避免detached HEAD状态

2. **定期同步**
   - 每天至少一次 `git fetch origin`
   - 重要操作前 `git pull`
   - 推送前确认本地最新

3. **清晰的分支策略**
   - master: 稳定版本
   - phase3-development: 开发分支
   - feature/*: 功能分支

## 会话开始检查清单

```bash
# 1. 检查当前状态
git status

# 2. 检查当前分支
git branch -a

# 3. 检查最近提交
git log --oneline -5

# 4. 检查远程状态
git fetch origin
git status

# 5. 如果在detached HEAD，立即修复
if ! git symbolic-ref -q HEAD; then
    echo "⚠️ Detached HEAD detected!"
    git checkout master
fi
```

## 常见问题处理

### Detached HEAD

**识别**:
```bash
git status
# 输出: HEAD detached at <commit>
```

**修复**:
```bash
# 方案1: 切换到master
git checkout master

# 方案2: 如果有重要修改，创建分支
git checkout -b temp-branch
git checkout master
git merge temp-branch
```

**预防**:
- 不要直接checkout到commit hash
- 使用分支名而不是commit hash
- 定期检查Git状态

### 本地与远程不同步

**识别**:
```bash
git fetch origin
git status
# 输出: Your branch is behind 'origin/master' by N commits
```

**修复**:
```bash
# 如果本地没有修改
git pull origin master

# 如果本地有修改
git stash
git pull origin master
git stash pop
```

### 意外的文件修改

**识别**:
```bash
git status
# 输出: Changes not staged for commit
```

**处理**:
```bash
# 查看具体修改
git diff

# 如果是不需要的修改
git checkout -- <file>

# 如果是需要的修改
git add <file>
git commit -m "description"
```

## 强制规则

1. ✅ 每次会话开始运行检查清单
2. ✅ 重要操作前确认在正确分支
3. ✅ 发现detached HEAD立即修复
4. ✅ 定期与远程同步
5. ✅ 不在detached HEAD状态工作
```

#### 2.3 扩展 `deployment-workflow.md`
**位置**: `~/.claude/rules/common/deployment-workflow.md`

**新增章节**:
```markdown
## 部署路径管理

### 路径规范

**前端**:
- 构建目录: `phase3/website/dist/`
- 部署目录: `/var/www/nautilus/current/`
- Nginx配置: `root /var/www/nautilus/current;`

**后端**:
- 代码目录: `~/nautilus-mvp/phase3/backend/`
- 服务名称: `nautilus-backend`
- 端口: 8000

### 部署脚本模板

```bash
#!/bin/bash
# deploy-website.sh

set -e  # 遇到错误立即退出

PROJECT_DIR="/c/Users/chunx/Projects/nautilus-core"
DEPLOY_DIR="/var/www/nautilus/current"
BACKUP_DIR="/var/www/nautilus/backup-$(date +%Y%m%d-%H%M%S)"

echo "📦 Building..."
cd "$PROJECT_DIR/phase3/website"
npm run build

echo "💾 Backing up..."
ssh cloud "cp -r $DEPLOY_DIR $BACKUP_DIR"

echo "🚀 Deploying..."
scp -r dist/* cloud:$DEPLOY_DIR/

echo "✅ Verifying..."
ssh cloud "ls -la $DEPLOY_DIR/"
curl -I https://www.nautilus.social/
curl https://www.nautilus.social/api/stats

echo "✅ Deployment complete!"
echo "Backup saved at: $BACKUP_DIR"
```

### 部署验证清单

- [ ] 构建成功（无错误）
- [ ] 文件在正确目录
- [ ] Nginx能访问
- [ ] 外网能访问
- [ ] 关键功能可用
- [ ] 备份已创建

### 回滚流程

```bash
# 如果部署失败，立即回滚
BACKUP_DIR="<最新备份目录>"
ssh cloud "rm -rf /var/www/nautilus/current/*"
ssh cloud "cp -r $BACKUP_DIR/* /var/www/nautilus/current/"
```
```

---

### 3️⃣ 应该创建的技能 (skills/)

#### 3.1 部署验证技能
**文件**: `~/.claude/agents/verify-deployment.md`

```markdown
---
name: verify-deployment
description: Verify deployment is successful and accessible
model: sonnet
---

# Deployment Verification Agent

You are a deployment verification specialist. Your job is to verify that a deployment was successful and the application is accessible.

## Verification Steps

1. **Check Build Output**
   - Look for errors in build logs
   - Verify build artifacts exist
   - Check file sizes are reasonable

2. **Check Deployment Directory**
   - Verify files are in correct location
   - Check file permissions
   - Verify all required files present

3. **Check Server Access**
   - Nginx can access files
   - Application responds to requests
   - No 404 or 500 errors

4. **Check External Access**
   - Website accessible from internet
   - API endpoints respond correctly
   - Key features work

5. **Check Content**
   - Key code exists in JS files
   - API returns expected data
   - No console errors

## Tools Available

- Bash: Run verification commands
- Read: Check log files
- Grep: Search for errors

## Output Format

Provide a clear verification report:

```
✅ Build: Success
✅ Deployment: Files in correct location
✅ Server Access: Nginx responding
✅ External Access: Website accessible
✅ Content: Key features present

Overall: PASS ✅
```

Or if issues found:

```
✅ Build: Success
❌ Deployment: Files in wrong location
   Expected: /var/www/nautilus/current/
   Actual: /var/www/nautilus/dist/

Overall: FAIL ❌

Action Required:
1. Move files to correct location
2. Restart Nginx
3. Re-verify
```

## Important

- Always check ALL steps
- Don't skip verification
- Report issues immediately
- Provide clear action items
```

#### 3.2 Git状态检查技能
**文件**: `~/.claude/agents/check-git-status.md`

```markdown
---
name: check-git-status
description: Check and fix Git repository state
model: haiku
---

# Git Status Check Agent

You are a Git state management specialist. Your job is to check the Git repository state and fix common issues.

## Check Steps

1. **Current Status**
   ```bash
   git status
   ```

2. **Current Branch**
   ```bash
   git branch
   git symbolic-ref -q HEAD || echo "⚠️ Detached HEAD!"
   ```

3. **Recent Commits**
   ```bash
   git log --oneline -5
   ```

4. **Remote Sync**
   ```bash
   git fetch origin
   git status
   ```

## Common Issues

### Detached HEAD
**Fix**:
```bash
git checkout master
```

### Behind Remote
**Fix**:
```bash
git pull origin master
```

### Uncommitted Changes
**Report**: List files and ask user what to do

## Output Format

```
Git Status Report:

Branch: master ✅
Detached HEAD: No ✅
Sync Status: Up to date ✅
Uncommitted Changes: None ✅

Overall: HEALTHY ✅
```

Or if issues:

```
Git Status Report:

Branch: (detached HEAD) ❌
Detached HEAD: Yes ❌
Sync Status: Behind by 5 commits ⚠️
Uncommitted Changes: 3 files ⚠️

Overall: NEEDS ATTENTION ❌

Recommended Actions:
1. Checkout master branch
2. Pull latest changes
3. Review uncommitted changes
```
```

#### 3.3 标准部署技能
**文件**: `~/.claude/agents/deploy-nautilus.md`

```markdown
---
name: deploy-nautilus
description: Deploy Nautilus website with verification
model: sonnet
---

# Nautilus Deployment Agent

You are a deployment specialist for the Nautilus project. Your job is to deploy the website safely with full verification.

## Deployment Steps

1. **Pre-deployment Check**
   - Check Git status (use check-git-status agent)
   - Verify on correct branch
   - Ensure no uncommitted changes

2. **Build**
   ```bash
   cd phase3/website
   npm run build
   ```
   - Check for errors
   - Verify dist/ directory created
   - Check file sizes

3. **Backup**
   ```bash
   ssh cloud "cp -r /var/www/nautilus/current /var/www/nautilus/backup-$(date +%Y%m%d-%H%M%S)"
   ```

4. **Deploy**
   ```bash
   scp -r dist/* cloud:/var/www/nautilus/current/
   ```

5. **Verify**
   - Use verify-deployment agent
   - Check all verification steps pass

6. **Report**
   - Provide deployment summary
   - Include backup location
   - List any issues

## Rollback Procedure

If verification fails:
```bash
# Find latest backup
ssh cloud "ls -lt /var/www/nautilus/ | grep backup | head -1"

# Restore backup
ssh cloud "rm -rf /var/www/nautilus/current/*"
ssh cloud "cp -r /var/www/nautilus/backup-YYYYMMDD-HHMMSS/* /var/www/nautilus/current/"
```

## Output Format

```
Nautilus Deployment Report

Pre-deployment: ✅
Build: ✅
Backup: ✅ (saved at backup-20260316-013000)
Deploy: ✅
Verification: ✅

Deployment: SUCCESS ✅

Website: https://www.nautilus.social/
Backup: /var/www/nautilus/backup-20260316-013000
```

## Important

- ALWAYS verify before declaring success
- ALWAYS create backup before deploying
- ALWAYS check all verification steps
- If ANY step fails, STOP and report
```

---

## 📋 实施计划

### Phase 1: 更新核心记忆 (今天)
1. ✅ 更新 `nautilus_project_status.md`
2. ✅ 创建 `deployment_failures_lessons.md`

### Phase 2: 更新规则 (今天)
1. ✅ 扩展 `verification-mandatory.md`
2. ✅ 创建 `git-state-management.md`
3. ✅ 扩展 `deployment-workflow.md`

### Phase 3: 创建技能 (明天)
1. ⏳ 创建 `verify-deployment` agent
2. ⏳ 创建 `check-git-status` agent
3. ⏳ 创建 `deploy-nautilus` agent

### Phase 4: 测试和验证 (明天)
1. ⏳ 测试部署验证技能
2. ⏳ 测试Git状态检查技能
3. ⏳ 测试完整部署流程

---

## 🎯 预期效果

### 短期效果
- 不再出现部署路径错误
- 不再出现detached HEAD问题
- 部署后立即发现问题

### 长期效果
- 部署流程标准化
- 问题自动检测
- 经验可复用

### 可衡量指标
- 部署成功率: 目标100%
- 问题发现时间: <5分钟
- 回滚时间: <2分钟

---

**创建时间**: 2026-03-16 01:45
**状态**: 待实施
