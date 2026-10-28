# Nautilus PPT 自动生成脚本

## 使用Google Slides API生成PPT

### 准备工作

1. **获取Google API凭证**:
   - 访问 https://console.cloud.google.com/
   - 启用Google Slides API
   - 创建OAuth 2.0凭证或API密钥

2. **安装依赖**:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 脚本结构

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# 初始化API
service = build('slides', 'v1', credentials=creds)

# 创建新演示文稿
presentation = service.presentations().create(body={
    'title': 'Nautilus - AI Agent Value Internet Platform'
}).execute()

presentation_id = presentation.get('presentationId')

# 添加16页内容
# 第1页: 封面
# 第2页: 问题
# ... 等等
```

### 我需要的信息

1. **API凭证**:
   - OAuth 2.0 token
   - 或者 API key
   - 或者 Service Account JSON

2. **权限**:
   - 创建Google Slides
   - 编辑Google Slides

### 完成后

- 生成Google Slides链接
- 可以在线编辑
- 可以导出为PPTX
- 可以导出为PDF
- 可以分享给投资人

---

## 替代方案: Python-PPTX

如果Google API不可用，我可以创建Python脚本直接生成.pptx文件。

```python
from pptx import Presentation
from pptx.util import Inches, Pt

# 创建演示文稿
prs = Presentation()
prs.slide_width = Inches(16)
prs.slide_height = Inches(9)

# 添加封面
title_slide_layout = prs.slide_layouts[0]
slide = prs.slides.add_slide(title_slide_layout)
title = slide.shapes.title
subtitle = slide.placeholders[1]

title.text = "Nautilus"
subtitle.text = "AI Agent价值互联网平台"

# ... 添加其他15页

# 保存
prs.save('Nautilus_Pitch_Deck.pptx')
```

---

## 下一步

请告诉我：
1. 你有Google Slides API访问权限吗？
2. 或者你有其他API？
3. 或者我创建Python脚本，你本地运行？

我准备好立即开始！
