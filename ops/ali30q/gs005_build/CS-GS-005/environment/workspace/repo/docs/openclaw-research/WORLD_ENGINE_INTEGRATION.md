# World Engine × Nautilus 知识图谱结合方案

> **调研日期**: 2026-03-22
> **主题**: 王飞飞 World Engine 开源研究 + GigaWorld-0 与 Nautilus 知识图谱的结合点分析
> **文件状态**: 初步方案

---

## 一、World Engine / GigaWorld-0 研究调研

### 1.1 项目定位

| 项目 | 定位 | 关联 |
|------|------|------|
| **WorldEngineAI** | Physical AGI Data Solutions（物理AGI数据基础设施） | 王飞飞等人创立 |
| **GigaWorld-0** | World Models as Data Engine for Embodied AI（arXiv:2511.19861） | Open-GigaAI 团队发布 |

**官网**: worldengine.ai — 创始团队来自自动驾驶与机器人行业头部机构。

### 1.2 GigaWorld-0 核心技术栈

GigaWorld-0 是当前最接近"World Engine"理念的开源实现，其框架分两大组件：

```
GigaWorld-0
├── GigaWorld-0-Video（视频生成引擎）
│   ├── GigaWorld-0-Video-Dreamer：Image-Text-to-Video 基础模型
│   ├── 61×480×640 @ 2B 参数
│   └── 功能：在精细控制下生成多样化、纹理丰富、时间连贯的具身场景视频
│
└── GigaWorld-0-3D（3D 仿真引擎）
    ├── 3D 生成建模
    ├── 3D Gaussian Splatting（三维场景重建）
    ├── 物理可微分系统辨识（differentiable physics）
    └── 可执行运动规划（executable motion planning）
```

**关键技术结论（来自论文 arXiv:2511.19861）**：
> 在 GigaWorld-0 生成的合成数据上训练的 VLA 模型（如 GigaBrain-0），在没有任何真实世界交互的情况下，在物理机器人上实现了强泛化能力和高任务成功率。

这意味着：**世界引擎可以替代大量真实物理数据**，是具身智能的"数据飞轮"。

### 1.3 World Engine 核心理念

```
World Engine = 物理世界的数字孪生引擎
    └── 目标：让 AI Agent 能在仿真环境中规划、验证、执行物理操作
    └── 核心价值：降低物理世界数据采集成本，实现"仿真到现实"(Sim2Real)闭环
```

| 能力 | 描述 |
|------|------|
| **视频生成** | 生成多样化具身场景视频（物体操控、移动导航、人机交互） |
| **3D 重建** | Gaussian Splatting 高质量物理场景 |
| **运动规划** | 基于物理模型的可执行动作序列 |
| **Sim2Real** | 合成数据 → 真实机器人泛化 |

### 1.4 技术依赖栈

```
GigaWorld-0 依赖:
├── GigaTrain    — 高效训练框架（FP8 精度 + 稀疏注意力，显存/算力大幅降低）
├── GigaDatasets — 数据策展、评估、可视化统一框架
└── GigaModels   — 多模态生成与感知模型仓库
```

---

## 二、Nautilus 知识图谱现状

### 2.1 当前 KG 实体类型

| 实体类型 | 包含实体 |
|----------|----------|
| **Agent** | leader, planner, executor, reviewer, memory |
| **Tool** | browser, code_interpreter, file_manager, api_client, database |
| **DataSource** | github, vector_db, blockchain |

### 2.2 当前 KG 关系类型

```
leader →(delegates)→ planner / executor / reviewer
planner →(assigns)→ executor
executor →(submits)→ reviewer
reviewer →(reports)→ leader
executor →(uses)→ browser / code_interpreter / file_manager
memory →(connects)→ vector_db
memory →(reads)→ github
```

### 2.3 当前局限

1. **纯数字世界**：只覆盖 API 调用、代码执行、文件操作，没有物理世界建模
2. **无仿真工具**：没有"模拟物理结果"、"生成合成数据"的执行器
3. **无具身概念**：KG 中没有空间位置、物体状态、动作序列等实体
4. **无 Sim2Real 通道**：无法将仿真结果映射回真实机器人执行

---

## 三、结合方案：World Model 融入 KG

### 3.1 架构整合总览

```
┌──────────────────────────────────────────────────────────────┐
│              Nautilus 知识图谱扩展层                           │
├──────────────┬─────────────────────┬────────────────────────┤
│  数字世界 KG  │   World Model KG    │  物理世界 KG          │
│  (现有)       │   (新增核心)         │  (新增)               │
├──────────────┼─────────────────────┼────────────────────────┤
│ Agent/Tool/  │ WorldModel          │ Robot                 │
│ DataSource   │ SimulationScenario  │ PhysicalObject        │
│              │ VLAPolicy           │ ActionSequence        │
│              │ TrajectoryData      │ SpaceRegion           │
└──────┬───────┴──────────┬──────────┴──────────┬────────────┘
       │                   │                      │
       │  ┌────────────────┘                      │
       │  │           World Engine 仿真层         │
       │  ├──────────────────────────────────────┤
       │  │  GigaWorld-0-Video (视频生成)         │
       │  │  GigaWorld-0-3D (3D + 运动规划)       │
       │  │  GigaTrain (高效训练推理)             │
       │  └──────────────────────────────────────┘
       │
       │  ┌──────────────────────────────────────┐
       └─►│  BBI Protocol (大脑-身体接口)        │
          │  ← Nautilus 任务请求                  │
          │  ← 机器人执行 → 仿真验证             │
          └──────────────────────────────────────┘
```

### 3.2 新增 KG 实体类型

```python
# KG 扩展：新增实体类型

PhysicalWorldEntities = {
    # ===== 仿真引擎层 =====
    "world_model": EntityType(
        id="world_model",
        type="WorldEngine",
        properties={
            "engine": "GigaWorld-0-Video | GigaWorld-0-3D",  # 引擎类型
            "version": "str",
            "capability": ["video_generation", "3d_reconstruction", 
                          "motion_planning", "physics_simulation"],
            "input_modality": "text | image | video | 3d_scan",
            "output_modality": "video | 3d_scene | trajectory",
        }
    ),
    
    "simulation_scenario": EntityType(
        id="simulation_scenario",
        type="SimulationScenario",
        properties={
            "scene_type": "kitchen | warehouse | street | factory | custom",
            "objects": ["list of object ids"],          # 场景中物体
            "initial_state": "dict of object states",
            "physics_params": {"gravity", "friction", "elasticity"},
            "agent_goal": "str (自然语言目标描述)",
            "succeeded": "bool",
        }
    ),
    
    "vla_policy": EntityType(
        id="vla_policy",
        type="VLAPolicy",
        properties={
            "policy_name": "str",
            "base_model": "GigaBrain-0 | GR1 | OpenVLA | π0",
            "training_data": "real | synthetic | mixed",
            "synthetic_data_source": "GigaWorld-0 generated",
            "success_rate": "float",
            "generalization_score": "float",
            "deployed_on": "robot_id",
        }
    ),
    
    "trajectory_data": EntityType(
        id="trajectory_data",
        type="TrajectoryData",
        properties={
            "source": "real_robot | world_model_simulation",
            "action_sequence": "list of (timestamp, action, state) tuples",
            "reward": "float",
            "task_description": "str",
            "robot_id": "str",
            "physical_feasibility": "bool",
        }
    ),
    
    # ===== 物理世界实体 =====
    "robot": EntityType(
        id="robot",
        type="Robot",
        properties={
            "robot_type": "humanoid | wheeled | arm | drone",
            "hardware_spec": {"actuators", "sensors", "degrees_of_freedom"},
            "current_policy": "vla_policy_id",
            "simulated_twin": "simulation_scenario_id",
        }
    ),
    
    "physical_object": EntityType(
        id="physical_object",
        type="PhysicalObject",
        properties={
            "category": "rigid | deformable | liquid",
            "properties": {"mass", "friction", "shape"},
            "current_location": "space_region_id",
            "state": "grasped | placed | fallen | moving",
        }
    ),
    
    "space_region": EntityType(
        id="space_region",
        type="SpaceRegion",
        properties={
            "region_type": "room | outdoor | vehicle_interior",
            "layout": "3d_coordinate_map",
            "contained_objects": ["physical_object_ids"],
            "access_points": ["navigation_targets"],
        }
    ),
    
    "action_sequence": EntityType(
        id="action_sequence",
        type="ActionSequence",
        properties={
            "steps": "list of ActionStep",
            "planned_by": "planner_agent_id | world_model_id",
            "validated_in": "simulation_scenario_id (if simulated)",
            "physical_executed": "bool",
            "execution_result": "success | partial | failed",
        }
    ),
}
```

### 3.3 新增 KG 关系类型

```python
# 新增关系扩展

WorldModelRelations = [
    # Agent ↔ WorldEngine
    ("planner", "uses", "world_model", "plans physical tasks using simulation"),
    ("executor", "uses", "world_model", "validates actions before execution"),
    ("reviewer", "queries", "trajectory_data", "reviews simulation results"),
    
    # Simulation flow
    ("vla_policy", "trained_on", "trajectory_data", "policy learned from trajectories"),
    ("trajectory_data", "generated_from", "simulation_scenario", "data created in simulation"),
    ("simulation_scenario", "governed_by", "world_model", "scenario runs in engine"),
    
    # Physical world binding
    ("robot", "runs", "vla_policy", "policy deployed on robot"),
    ("robot", "has_twin", "simulation_scenario", "digital twin of physical robot"),
    ("physical_object", "located_in", "space_region", "object in spatial region"),
    ("action_sequence", "executed_on", "physical_object", "action targets object"),
    ("action_sequence", "planned_for", "robot", "action designed for robot"),
    ("vla_policy", "validates_in", "simulation_scenario", "policy tested before deploy"),
    
    # Cross-verification (Raid extension for physics)
    ("action_sequence", "cross_validated_by", "world_model", "world model confirms feasibility"),
    ("trajectory_data", "cross_validated_by", "reviewer", "agent reviews trajectory"),
    
    # Task decomposition
    ("task", "decomposed_to", "action_sequence", "high-level task broken into actions"),
]
```

---

## 四、具体集成场景

### 场景 1：Agent 请求物理任务验证（核心场景）

```
用户: "让机器人把桌上的咖啡杯放到水槽里"
```

```
Step 1: leader 理解任务
  → KG: 新增 entity task_physical_001 (type="task", task_type="PHYSICAL")
  → relation: leader →(assigns)→ planner

Step 2: planner 使用 World Model 仿真验证
  → KG: 新增 simulation_scenario_001
  → planner →(uses)→ world_model
  → world_model 运行 GigaWorld-0-3D：
    - 输入：场景描述（桌子、咖啡杯、水槽）
    - 输出：action_sequence_001（动作序列 + 可行性评分）
  → KG: action_sequence_001 关联到 simulation_scenario_001
  → 可行性 < 阈值？→ 返回 planner 重规划

Step 3: Raid 3 审查（新增物理审查层）
  → reviewer 查询 world_model 的仿真结果
  → reviewer 对比 trajectory_data 历史成功率
  → Raid 投票决定是否执行

Step 4: 通过 BBI Protocol 发送到机器人
  → action_sequence_001 →(executed_on)→ robot_001
  → 机器人执行物理动作 → sensor_data 回传

Step 5: 执行结果写入 KG
  → trajectory_data_actual = 实际执行的轨迹
  → trajectory_data_actual →(cross_validated_by)→ simulation_scenario_001
  → 用于下次规划的数据积累
```

### 场景 2：World Model 作为执行工具（类比 code_interpreter）

```python
class WorldModelExecutor:
    """
    作为 Nautilus Agent Team 中的一个新的 Executor 角色
    类比现有的 CodeExecutor / BrowserExecutor
    """
    def __init__(self, engine="GigaWorld-0"):
        self.engine = engine  # GigaWorld-0-Video 或 GigaWorld-0-3D
    
    def execute(self, task: dict) -> dict:
        """
        输入:
          task = {
            "goal": "pick up the red cup",
            "scene_description": "kitchen counter with cup",
            "robot_spec": "dual-arm manipulator",
            "output_type": "trajectory | video | 3d_scene"
          }
        返回:
          result = {
            "status": "success | infeasible | ambiguous",
            "action_sequence": [...],
            "feasibility_score": 0.92,
            "generated_data": { ... }
          }
        """
        # 调用 GigaWorld-0
        ...
```

**KG 中的角色定位**：
```
executor →(has_capability)→ world_model_executor
planner →(selects)→ world_model_executor  (当 task_type = PHYSICAL)
```

### 场景 3：Nautilus Raid × World Model 验证层

现有的 Raid 机制（多 Agent 交叉验证）可以扩展，加入物理验证层：

```
Raid-Physical-3 协议：
┌─────────────────────────────────────────────────┐
│  Raid-Physical-3 (3 Agent 多数投票)            │
├─────────────────────────────────────────────────┤
│  Agent A (Executor): 提出动作序列               │
│  Agent B (Reviewer): 用 World Model 仿真验证   │
│  Agent C (Memory): 查询历史相似任务成功率      │
│                                                 │
│  3 取 2 → 决定执行 / 拒绝 / 重规划              │
└─────────────────────────────────────────────────┘
```

### 场景 4：知识图谱 × 世界模型 联合推理

当前 KG 的 `suggest_next_actions` 可以扩展，结合 World Model：

```python
def suggest_next_actions_physical(entity_id: str, kg: KnowledgeGraph, 
                                   world_model) -> list:
    """扩展的动作推荐：结合 KG 关系 + 世界模型仿真"""
    entity = kg.get_entity(entity_id)
    
    if entity.get("type") == "task":
        task_type = entity["properties"].get("task_type")
        
        if task_type == "PHYSICAL":
            # 用 World Model 生成候选动作
            scene = entity["properties"].get("scene_description")
            candidates = world_model.generate_action_candidates(scene)
            
            # 用 KG 历史验证每个候选
            validated = []
            for action in candidates:
                history = kg.query_relations(
                    from_id=action["id"], 
                    relation_type="executed_successfully"
                )
                if history or world_model.validate_physical(action):
                    validated.append(action)
            return validated
    
    return kg.suggest_next_actions(entity_id)  # 降级到原有逻辑
```

---

## 五、实施路线图

### Phase 1：KG Schema 扩展（1-2 周）

```python
# 优先级 P0：扩展 KG 支持物理世界实体
EXTENDED_ENTITIES = {
    # 新增实体类型
    "WorldEngine": {...},
    "SimulationScenario": {...},
    "VLAPolicy": {...},
    "TrajectoryData": {...},
    "Robot": {...},
    "PhysicalObject": {...},
    "SpaceRegion": {...},
    "ActionSequence": {...},
}

EXTENDED_RELATIONS = {
    # 新增关系
    "uses_world_model",
    "trained_on_trajectory",
    "generated_in_simulation",
    "deployed_on_robot",
    "has_digital_twin",
    "cross_validated_by_world_model",
    "physical_executed",
}
```

**交付物**：`knowledge_graph.py` 新增实体/关系操作方法

### Phase 2：World Model Executor（2-3 周）

```python
# 新增 world_model_executor.py
class WorldModelExecutor:
    def __init__(self, 
                 engine_url: str = "localhost:8080",
                 engine_type: str = "GigaWorld-0-Video"):
        self.engine_type = engine_type
    
    def generate_trajectory(self, scene: dict, goal: str) -> TrajectoryData:
        """生成动作轨迹（调用 GigaWorld-0-3D）"""
        ...
    
    def generate_video(self, scene: dict, action: str) -> bytes:
        """生成仿真视频（调用 GigaWorld-0-Video）"""
        ...
    
    def validate_action(self, action: ActionSequence, 
                       robot: Robot) -> float:
        """验证动作的物理可行性"""
        ...
```

**交付物**：`world_model_executor.py` + `test_world_model.py`

### Phase 3：BBI Protocol × World Model 集成（2 周）

扩展现有的 Brain-Body Interface 协议，加入仿真验证步骤：

```python
# BBI 扩展消息类型
EXTENDED_BBI_MESSAGES = {
    "simulation_request": {
        "scene_description": "...",
        "goal": "...",
        "robot_spec": "...",
    },
    "simulation_result": {
        "feasibility": 0.92,
        "action_sequence": [...],
        "predicted_outcome": "success",
        "risk_factors": ["obstacle in path"],
    }
}
```

**交付物**：`brain_body_interface.py` 新增 `simulation_request` / `simulation_result` 处理

### Phase 4：Raid-Physical 审查层（2 周）

```python
# Raid-Physical 审查机制
class RaidPhysicalReviewer:
    """专门负责物理任务审查的 Reviewer Agent"""
    
    async def review_physical_task(self, action_seq: ActionSequence) -> dict:
        # 1. 查 KG 历史相似任务
        similar = self.kg.query_similar_tasks(action_seq.description)
        
        # 2. World Model 仿真验证
        sim_result = self.world_model.validate(action_seq)
        
        # 3. 多数投票
        votes = [
            self._check_history_success_rate(similar),
            self._check_simulation_feasibility(sim_result),
            self._check_physical_constraints(action_seq),
        ]
        
        return {"approved": sum(votes) >= 2, "votes": votes}
```

### Phase 5：联合推理 API（2 周）

```python
# 暴露给 Agent Team 的统一推理接口
class WorldKGIntegration:
    """
    知识图谱 × 世界模型 联合推理引擎
    """
    
    def query_with_simulation(self, entity_id: str, 
                              simulation_goal: str) -> dict:
        """KG 查询 + 物理仿真联合"""
        # 1. 从 KG 获取相关实体和关系
        kg_context = self.kg.get_related_entities(entity_id, depth=2)
        
        # 2. 构建仿真场景
        scene = self._build_scene_from_kg(kg_context)
        
        # 3. 运行 World Model
        sim_result = self.world_model.generate(scene, simulation_goal)
        
        # 4. 合并结果
        return {**kg_context, "simulation": sim_result}
    
    def plan_physical_task(self, task: dict) -> ActionSequence:
        """物理任务规划（结合 KG 知识 + 世界模型仿真）"""
        ...
```

---

## 六、技术依赖与风险

### 6.1 依赖项

| 依赖 | 说明 | 优先级 |
|------|------|--------|
| GigaWorld-0 开源模型 | 需部署 GigaTrain/GigaWorld-0 | P0 |
| GPU 资源 | 视频生成和 3D 推理需要 CUDA | P0 |
| BBI Protocol | 现有 Brain-Body 接口 | P1（已实现） |
| Nautilus KG | 现有知识图谱 | P1（已实现） |
| 高质量 3D 场景数据 | 场景重建需要输入数据 | P2 |

### 6.2 风险

| 风险 | 影响 | 缓解方案 |
|------|------|----------|
| GigaWorld-0 算力成本高 | 每次仿真调用昂贵 | 使用 GigaTrain FP8 优化；异步批量处理 |
| World Model 幻觉 | 仿真结果不反映真实物理 | Raid 审查 + 真实机器人回传校正 |
| 仿真-现实差距(Sim2Real gap) | 仿真成功但真实失败 | 渐进式部署：小范围真实验证 → 扩大 |
| 实时性不足 | 复杂场景仿真耗时 | 降级：快速度量估算（接触力、空间可达性）|

---

## 七、核心结论

> **World Engine（GigaWorld-0）和 Nautilus 知识图谱天然互补：**
> - **World Engine** = 物理世界的**因果仿真**（"这样运动会发生什么"）
> - **Knowledge Graph** = 物理世界的**语义建模**（"这个场景里有什么，它们是什么关系"）
> - **Raid 机制** = 物理决策的**验证层**（"仿真结果可信吗"）
> - **BBI Protocol** = 数字到物理的**执行通道**（"执行后回传真实结果"）

两者结合后，Nautilus 不再只是"数字 Agent 执行数字任务"，而是成为：
> **具备物理世界推理能力的通用 Agent 协作系统**，可在仿真中规划、在真实中执行、在 KG 中学习。

---

## 附录：参考资源

| 资源 | 链接 |
|------|------|
| GigaWorld-0 论文 | https://arxiv.org/abs/2511.19861 |
| GigaWorld-0 GitHub | https://github.com/open-gigaai/giga-world-0 |
| GigaWorld-0 项目页 | https://giga-world-0.github.io/ |
| GigaWorld-0 HuggingFace | https://huggingface.co/open-gigaai |
| WorldEngineAI 官网 | https://www.worldengine.ai/ |
