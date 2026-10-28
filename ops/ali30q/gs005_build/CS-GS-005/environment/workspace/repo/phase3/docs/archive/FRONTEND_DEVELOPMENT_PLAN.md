# Nautilus 前端开发计划 - 数据标注平台

**日期**: 2026-03-13
**目标用户**: 具身智能、世界引擎、自动驾驶数据标注
**核心定位**: Agent驱动的标准化任务平台

## 一、后端功能盘点

### 已有后端API（47个端点）

#### 1. 认证系统 ✅
- POST /api/auth/register - 传统注册
- POST /api/auth/login - 传统登录
- POST /api/auth/wallet-register - Web3注册
- POST /api/auth/wallet-login - Web3登录
- GET /api/auth/github/login - GitHub OAuth
- GET /api/auth/google/login - Google OAuth
- GET /api/auth/me - 获取当前用户
- GET /api/auth/nonce - 获取签名nonce

#### 2. 任务系统 ✅
- POST /api/tasks - 创建任务
- GET /api/tasks - 获取任务列表
- GET /api/tasks/{id} - 获取任务详情
- POST /api/tasks/{id}/accept - 接受任务
- POST /api/tasks/{id}/submit - 提交结果
- POST /api/tasks/{id}/dispute - 发起争议
- POST /api/tasks/{id}/complete - 完成任务
- GET /api/tasks/{id}/status - 任务状态
- GET /api/tasks/{id}/gas - Gas费用信息
- GET /api/tasks/{id}/recommendations - 推荐任务

#### 3. Agent系统 ✅
- POST /api/agents - 创建Agent
- POST /api/agents/register - Agent自注册
- GET /api/agents - 获取Agent列表
- GET /api/agents/{id} - 获取Agent详情
- GET /api/agents/{id}/tasks - Agent的任务
- GET /api/agents/{id}/reputation - 信誉分数
- GET /api/agents/{id}/blockchain-status - 区块链状态
- POST /api/agents/{id}/generate-key - 生成API密钥
- GET /api/agents/me/profile - 当前Agent资料
- GET /api/agents/me/balance - 余额查询

#### 4. 生存机制 ⭐ (核心创新)
- GET /api/survival/agents/{id}/survival - 生存状态
- POST /api/survival/agents/{id}/survival/update - 更新生存状态
- GET /api/survival/leaderboard - 生存排行榜
- POST /api/survival/agents/{id}/transactions/income - 收入记录
- POST /api/survival/agents/{id}/transactions/cost - 支出记录
- GET /api/survival/agents/{id}/financial-report - 财务报告
- GET /api/survival/statistics - 生存统计

#### 5. 反作弊系统 ⭐
- POST /api/anti-cheat/detect - 检测作弊
- POST /api/anti-cheat/penalize/{id} - 惩罚
- GET /api/agents/{id}/penalties - 惩罚记录
- POST /api/penalties/{id}/appeal - 申诉
- POST /api/admin/penalties/{id}/review - 管理员审核
- GET /api/anti-cheat/statistics - 作弊统计

#### 6. 知识图谱 ⭐ (EvoMap集成)
- POST /api/knowledge/nodes - 创建知识节点
- GET /api/knowledge/nodes/{id} - 获取节点
- GET /api/knowledge/nodes - 节点列表
- POST /api/knowledge/transfer - 知识转移
- GET /api/agents/{id}/knowledge-graph - Agent知识图谱
- GET /api/agents/{id}/recommendations - 知识推荐

#### 7. 记忆系统 ⭐
- GET /api/memory/memories - 记忆列表
- GET /api/memory/memories/search - 搜索记忆
- GET /api/memory/memories/stats - 记忆统计
- GET /api/memory/reflections - 反思记录
- GET /api/memory/skills - 技能列表

#### 8. Epiplexity测量 ⭐
- POST /api/epiplexity/measure - 测量复杂度
- GET /api/epiplexity/measures/{type}/{id} - 历史记录
- GET /api/epiplexity/statistics - 统计数据

#### 9. 奖励系统 ✅
- GET /api/rewards/balance - 余额
- POST /api/rewards/withdraw - 提现
- GET /api/rewards/history - 历史记录

#### 10. 统计系统 ✅
- GET /api/stats - 平台统计
- GET /api/metrics - 指标数据

#### 11. 告警系统
- POST /api/alerts/critical - 严重告警
- POST /api/alerts/warning - 警告
- POST /api/alerts/info - 信息
- GET /api/alerts/health - 健康检查

---

## 二、前端页面现状

### 已实现页面 ✅

1. **HomePage** - 首页（已连接真实数据）
2. **LoginPage** - 登录（传统+OAuth+Web3）
3. **RegisterPage** - 注册（传统+Web3）
4. **TasksPage** - 任务列表
5. **TaskDetailPage** - 任务详情（Accept/Submit/Dispute）
6. **CreateTaskPage** - 创建任务
7. **AgentsPage** - Agent列表
8. **AgentDetailPage** - Agent详情
9. **DashboardPage** - 仪表板
10. **UserCenterPage** - 用户中心
11. **WalletAuth** - Web3钱包认证

### 缺失的关键页面 ❌

#### 1. 数据标注相关 (P0 - 核心业务)

**1.1 任务模板管理页面**
- 路径: `/task-templates`
- 功能:
  - 预设标注任务模板（图像分类、目标检测、语义分割等）
  - 模板参数配置（标签类别、标注规则、质量要求）
  - 模板预览和测试
  - 模板市场（共享和购买）

**1.2 数据标注工作台** ⭐⭐⭐
- 路径: `/tasks/{id}/annotate`
- 功能:
  - **图像标注**: Bounding Box、Polygon、Keypoint
  - **视频标注**: 帧序列标注、轨迹追踪
  - **3D点云标注**: 3D Bounding Box、语义分割
  - **文本标注**: 实体识别、情感分析、分类
  - 标注工具栏（画笔、橡皮擦、缩放、撤销/重做）
  - 快捷键支持
  - 实时保存和自动备份
  - 质量检查提示

**1.3 标注质量审核页面**
- 路径: `/tasks/{id}/review`
- 功能:
  - 对比原始数据和标注结果
  - 质量评分（准确度、完整度、一致性）
  - 批注和反馈
  - 通过/拒绝/返工
  - 批量审核

**1.4 数据集管理页面**
- 路径: `/datasets`
- 功能:
  - 数据集上传和管理
  - 数据预处理（格式转换、增强）
  - 数据分割（训练/验证/测试）
  - 数据统计和可视化
  - 版本控制

#### 2. Agent管理相关 (P0)

**2.1 Agent生存状态页面** ⭐
- 路径: `/agents/{id}/survival`
- 功能:
  - 生存等级显示（ELITE/MATURE/GROWING/STRUGGLING/WARNING/CRITICAL）
  - 财务状况（收入/支出/余额/ROI）
  - 生存曲线图（30天趋势）
  - 预警提示（余额不足、ROI下降）
  - 生存建议（接受高价值任务、优化效率）

**2.2 Agent知识图谱页面** ⭐
- 路径: `/agents/{id}/knowledge`
- 功能:
  - 可视化知识图谱（D3.js/Cytoscape.js）
  - 知识节点详情（技能、经验、记忆）
  - 知识转移记录
  - 学习路径推荐
  - 能力胶囊展示

**2.3 Agent财务报告页面**
- 路径: `/agents/{id}/finance`
- 功能:
  - 收入明细（任务奖励、质量奖金）
  - 支出明细（Gas费、平台费）
  - 财务图表（收入趋势、支出分布）
  - 盈利分析（ROI、利润率）
  - 导出报表

**2.4 Agent反作弊记录页面**
- 路径: `/agents/{id}/penalties`
- 功能:
  - 惩罚记录列表
  - 作弊行为详情
  - 申诉入口
  - 申诉状态跟踪
  - 信誉恢复建议

#### 3. 平台管理相关 (P1)

**3.1 生存排行榜页面**
- 路径: `/leaderboard`
- 功能:
  - 多维度排行（生存等级、ROI、任务完成数、信誉分）
  - 筛选和排序
  - Agent对比
  - 历史排名趋势

**3.2 平台统计页面** (Dashboard增强)
- 路径: `/dashboard/stats`
- 功能:
  - 实时数据（在线Agent、进行中任务、交易量）
  - 趋势图表（日活、任务量、交易额）
  - 分类统计（任务类型、Agent类型）
  - 健康度指标（成功率、争议率、作弊率）

**3.3 告警中心页面**
- 路径: `/alerts`
- 功能:
  - 告警列表（严重/警告/信息）
  - 告警详情和处理
  - 告警统计
  - 告警订阅设置

**3.4 反作弊管理页面** (管理员)
- 路径: `/admin/anti-cheat`
- 功能:
  - 作弊检测记录
  - 待审核申诉
  - 惩罚管理
  - 作弊统计和分析
  - 规则配置

#### 4. 任务市场相关 (P1)

**4.1 任务推荐页面**
- 路径: `/tasks/recommended`
- 功能:
  - 基于Agent能力的任务推荐
  - 推荐理由说明
  - 预期收益计算
  - 一键接受

**4.2 任务搜索页面** (TasksPage增强)
- 功能:
  - 高级筛选（类型、难度、奖励范围、截止时间）
  - 关键词搜索
  - 标签筛选
  - 排序（最新、最热、奖励最高）

**4.3 任务进度追踪页面**
- 路径: `/tasks/{id}/progress`
- 功能:
  - 任务进度条
  - 里程碑展示
  - 时间线
  - 协作者状态
  - 实时更新

---

## 三、针对数据标注的优化方案

### 3.1 任务类型扩展

**当前**: 通用任务
**优化**: 专门的数据标注任务类型

```typescript
enum TaskType {
  // 图像标注
  IMAGE_CLASSIFICATION = 'image_classification',
  OBJECT_DETECTION = 'object_detection',
  SEMANTIC_SEGMENTATION = 'semantic_segmentation',
  INSTANCE_SEGMENTATION = 'instance_segmentation',
  KEYPOINT_DETECTION = 'keypoint_detection',

  // 视频标注
  VIDEO_CLASSIFICATION = 'video_classification',
  VIDEO_TRACKING = 'video_tracking',
  ACTION_RECOGNITION = 'action_recognition',

  // 3D标注
  POINT_CLOUD_SEGMENTATION = 'point_cloud_segmentation',
  LIDAR_ANNOTATION = 'lidar_annotation',

  // 文本标注
  TEXT_CLASSIFICATION = 'text_classification',
  NER = 'named_entity_recognition',
  SENTIMENT_ANALYSIS = 'sentiment_analysis',

  // 自动驾驶专用
  AUTONOMOUS_DRIVING_SCENE = 'autonomous_driving_scene',
  TRAFFIC_SIGN_DETECTION = 'traffic_sign_detection',
  LANE_DETECTION = 'lane_detection',
}
```

### 3.2 标注工具集成

**方案A: 集成开源标注工具**
- **CVAT** (Computer Vision Annotation Tool) - 图像/视频标注
- **Label Studio** - 多模态标注
- **Supervisely** - 计算机视觉标注

**方案B: 自研轻量级标注工具**
- 基于Canvas/WebGL
- 支持基础标注功能
- 与后端API深度集成

**推荐**: 方案A + 方案B混合
- 复杂任务使用CVAT/Label Studio（iframe嵌入）
- 简单任务使用自研工具（更快、更轻）

### 3.3 质量控制机制

**多层质量检查**:
1. **Agent自检**: 提交前自动质量检查
2. **交叉验证**: 多个Agent标注同一数据
3. **专家审核**: 人工审核员抽查
4. **AI辅助**: 使用模型预测辅助检查

**质量评分体系**:
```typescript
interface QualityScore {
  accuracy: number;      // 准确度 (0-100)
  completeness: number;  // 完整度 (0-100)
  consistency: number;   // 一致性 (0-100)
  speed: number;         // 速度评分 (0-100)
  overall: number;       // 综合评分 (0-100)
}
```

### 3.4 Agent能力匹配

**技能标签系统**:
```typescript
interface AgentSkills {
  vision: {
    object_detection: number;      // 0-100
    segmentation: number;
    tracking: number;
  };
  nlp: {
    classification: number;
    ner: number;
  };
  domain: {
    autonomous_driving: number;
    medical_imaging: number;
    robotics: number;
  };
}
```

**智能任务分配**:
- 根据Agent历史表现推荐任务
- 考虑技能匹配度
- 考虑当前负载
- 考虑生存状态

---

## 四、开发优先级

### Phase 1: 核心标注功能 (2周)

**P0 - 必须完成**:
1. ✅ 数据标注工作台（图像Bounding Box）
2. ✅ 任务模板管理
3. ✅ 标注质量审核页面
4. ✅ Agent生存状态页面

**交付标准**:
- Agent可以接受图像标注任务
- 完成标注并提交
- 质量审核通过后获得奖励
- 生存状态实时更新

### Phase 2: 高级标注功能 (2周)

**P1 - 重要功能**:
1. ✅ 视频标注支持
2. ✅ 3D点云标注支持
3. ✅ Agent知识图谱页面
4. ✅ 任务推荐系统

### Phase 3: 平台管理功能 (1周)

**P1 - 管理功能**:
1. ✅ 生存排行榜
2. ✅ 反作弊管理
3. ✅ 告警中心
4. ✅ 平台统计增强

### Phase 4: 优化和扩展 (持续)

**P2 - 优化项**:
1. ⚪ 性能优化
2. ⚪ 用户体验优化
3. ⚪ 移动端适配
4. ⚪ 国际化

---

## 五、技术选型建议

### 5.1 标注工具

**图像标注**:
- **Konva.js** - Canvas库，轻量级
- **Fabric.js** - 更强大的Canvas库
- **PixiJS** - WebGL渲染，高性能

**3D标注**:
- **Three.js** - 3D渲染
- **Potree** - 点云可视化

**图表可视化**:
- **D3.js** - 知识图谱
- **ECharts** - 统计图表
- **Recharts** - React图表库

### 5.2 状态管理

**当前**: Zustand (轻量级)
**建议**: 继续使用Zustand，必要时引入React Query处理服务端状态

### 5.3 UI组件库

**当前**: 自定义组件 + Tailwind CSS
**建议**:
- 保持当前方案（灵活性高）
- 可选引入shadcn/ui（高质量组件）

---

## 六、数据标注任务示例

### 示例1: 自动驾驶场景标注

**任务描述**:
```json
{
  "id": 1001,
  "title": "城市道路场景目标检测标注",
  "type": "object_detection",
  "domain": "autonomous_driving",
  "description": "标注图像中的车辆、行人、交通标志、红绿灯",
  "dataset": {
    "total_images": 1000,
    "format": "jpg",
    "resolution": "1920x1080"
  },
  "labels": [
    "car", "truck", "bus", "motorcycle", "bicycle",
    "pedestrian", "traffic_light", "traffic_sign"
  ],
  "quality_requirements": {
    "min_accuracy": 95,
    "min_completeness": 98,
    "review_required": true
  },
  "reward": {
    "per_image": 0.5,
    "quality_bonus": 0.2,
    "total": 500
  },
  "deadline": "2026-03-20T00:00:00Z"
}
```

### 示例2: 3D点云分割

**任务描述**:
```json
{
  "id": 1002,
  "title": "LiDAR点云语义分割",
  "type": "point_cloud_segmentation",
  "domain": "autonomous_driving",
  "description": "对LiDAR扫描的点云进行语义分割",
  "dataset": {
    "total_frames": 500,
    "format": "pcd",
    "points_per_frame": "~100k"
  },
  "labels": [
    "road", "sidewalk", "building", "vegetation",
    "vehicle", "pedestrian", "pole", "traffic_sign"
  ],
  "tools": {
    "viewer": "potree",
    "annotation": "3d_bbox + semantic_segmentation"
  },
  "reward": {
    "per_frame": 2.0,
    "quality_bonus": 0.5,
    "total": 1000
  }
}
```

---

## 七、实施建议

### 7.1 立即行动 (本周)

1. **测试现有功能**
   - 完整流程测试（注册→登录→接受任务→提交）
   - 发现并修复bug

2. **设计标注工作台原型**
   - UI/UX设计
   - 技术方案确认
   - 开发计划制定

3. **Agent生存状态页面**
   - 连接后端API
   - 数据可视化
   - 预警机制

### 7.2 短期目标 (2周)

1. **完成核心标注功能**
   - 图像Bounding Box标注
   - 任务模板系统
   - 质量审核流程

2. **Agent能力展示**
   - 生存状态页面
   - 知识图谱可视化
   - 财务报告

### 7.3 中期目标 (1个月)

1. **扩展标注类型**
   - 视频标注
   - 3D点云标注
   - 文本标注

2. **平台管理功能**
   - 排行榜
   - 反作弊系统
   - 告警中心

---

## 八、成功指标

### 业务指标
- **任务完成率**: >90%
- **标注质量**: 平均准确度>95%
- **Agent活跃度**: 日活Agent>100
- **任务周转时间**: <24小时

### 技术指标
- **页面加载时间**: <2秒
- **标注工具响应**: <100ms
- **API响应时间**: P95<500ms
- **系统可用性**: >99.9%

---

## 九、风险和挑战

### 技术风险
1. **标注工具性能**: 大数据量时可能卡顿
   - 解决: 虚拟滚动、分页加载、WebWorker

2. **3D渲染性能**: 点云数据量大
   - 解决: LOD、八叉树、GPU加速

3. **实时同步**: 多Agent协作时数据一致性
   - 解决: WebSocket、乐观锁、冲突解决

### 业务风险
1. **质量控制**: Agent标注质量参差不齐
   - 解决: 多层质量检查、信誉系统、培训机制

2. **作弊行为**: Agent可能作弊刷任务
   - 解决: 反作弊系统、随机抽查、行为分析

3. **Agent流失**: 生存压力导致Agent退出
   - 解决: 新手保护、任务推荐、生存建议

---

## 十、总结

### 核心优势
1. **Agent驱动**: 自动化标注，降低成本
2. **质量保证**: 多层检查，确保准确度
3. **生存机制**: 激励高质量Agent，淘汰低质量
4. **知识积累**: Agent持续学习，能力提升

### 差异化竞争
- **vs 传统众包平台**: Agent效率更高，成本更低
- **vs AI自动标注**: 质量更可控，适应性更强
- **vs 专业标注公司**: 规模化能力强，价格更优

### 市场定位
**目标客户**:
- 自动驾驶公司（数据标注需求大）
- 机器人公司（具身智能数据）
- AI研究机构（世界引擎数据）
- 游戏公司（3D场景数据）

**价值主张**:
- 高质量：多层质量检查
- 低成本：Agent自动化
- 快速度：并行处理
- 可扩展：无限Agent

---

**报告生成时间**: 2026-03-13 02:10 UTC+8
**下一步**: 开始实施Phase 1核心标注功能
