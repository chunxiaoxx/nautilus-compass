# Google Slides API 使用说明

**问题**: Google Slides API不支持API Key，需要OAuth2认证

---

## ⚠️ 当前状态

**Google Slides API**:
- ❌ API Key不支持
- ✅ 需要OAuth2认证
- ⚠️ 配置较复杂

**解决方案**:
1. 使用本地Python生成（推荐）
2. 配置OAuth2认证（复杂）

---

## ✅ 推荐方案：使用本地Python生成

### 优势

- ✅ 无需OAuth2配置
- ✅ 5分钟完成
- ✅ 立即可用
- ✅ 生成.pptx文件
- ✅ 可离线使用

### 立即执行

```bash
cd C:/Users/chunx/Projects/nautilus-core/docs
python generate_pitch_deck.py
```

**输出**:
- Nautilus_Pitch_Deck_CN.pptx
- 16页完整内容
- 专业配色和布局

---

## 🔧 如果需要Google Slides

### 需要配置OAuth2

**步骤**:
1. 访问 Google Cloud Console
2. 创建OAuth 2.0客户端ID
3. 下载credentials.json
4. 运行OAuth授权流程

**复杂度**: 高
**时间**: 30-60分钟

---

## 💡 建议

**立即使用本地Python方案**:
- 最快速度
- 最简单
- 最可靠

**生成后可以**:
- 上传到Google Drive
- 转换为Google Slides
- 在线编辑

---

## 🚀 立即行动

```bash
# 生成PPT
cd C:/Users/chunx/Projects/nautilus-core/docs
python generate_pitch_deck.py

# 打开查看
start Nautilus_Pitch_Deck_CN.pptx
```

**5分钟完成，立即可用！**
