# Nautilus 记忆系统创新点与差异化

**文档版本**: 1.0.0
**创建日期**: 2026-03-03

---

## 1. 核心创新点

### 1.1 Agent 协作记忆网络

**创新描述**: 不同于传统的单 Agent 记忆系统，Nautilus 构建跨 Agent 的协作记忆网络

**实现方案**:

```python
# services/collaborative_memory_service.py

class CollaborativeMemoryService:
    """Agent 协作记忆服务"""

    def share_success_pattern(
        self,
        source_agent_id: int,
        task_id: int,
        pattern: Dict[str, Any]
    ):
        """
        分享成功模式到记忆网络

        Args:
            source_agent_id: 源 Agent ID
            task_id: 任务 ID
            pattern: 成功模式
        """
        # 1. 提取可复用的模式
        reusable_pattern = self._extract_reusable_pattern(pattern)

        # 2. 生成嵌入
        embedding = self.embedding_service.encode(
            reusable_pattern["description"]
        )

        # 3. 存储到共享记忆池
        self.vector_store.upsert(
            agent_id=0,  # 0 表示共享记忆
            memory_type="shared_pattern",
            content=reusable_pattern["description"],
            embedding=embedding,
            metadata={
                "source_agent": source_agent_id,
                "task_id": task_id,
                "task_type": pattern["task_type"],
                "success_rate": pattern["success_rate"],
                "usage_count": 0,
                "pattern_data": reusable_pattern
            }
        )

    def learn_from_network(
        self,
        agent_id: int,
        task_description: str
    ) -> List[Dict[str, Any]]:
        """
        从协作网络学习

        Args:
            agent_id: Agent ID
            task_description: 任务描述

        Returns:
            相关的成功模式列表
        """
        # 1. 搜索共享记忆池
        query_embedding = self.embedding_service.encode(task_description)

        shared_patterns = self.vector_store.search(
            query_embedding=query_embedding,
            agent_id=0,  # 搜索共享记忆
            memory_type="shared_pattern",
            top_k=5
        )

        # 2. 过滤高质量模式
        quality_patterns = [
            p for p in shared_patterns
            if p["metadata"]["success_rate"] > 0.8
        ]

        # 3. 更新使用计数
        for pattern in quality_patterns:
            self._increment_usage_count(pattern["id"])

        return quality_patterns

    def _extract_reusable_pattern(self, pattern: Dict) -> Dict:
        """提取可复用的模式"""
        return {
            "description": pattern["description"],
            "task_type": pattern["task_type"],
            "strategy": pattern["strategy"],
            "key_steps": pattern["key_steps"],
            "common_pitfalls": pattern.get("pitfalls", []),
            "best_practices": pattern.get("best_practices", [])
        }

    def get_network_insights(self, task_type: str) -> Dict[str, Any]:
        """获取网络洞察"""
        # 统计该任务类型的共享模式
        patterns = self.vector_store.get_agent_memories(
            agent_id=0,
            memory_type="shared_pattern"
        )

        task_patterns = [
            p for p in patterns
            if p["metadata"]["task_type"] == task_type
        ]

        # 分析
        total_patterns = len(task_patterns)
        avg_success_rate = np.mean([
            p["metadata"]["success_rate"]
            for p in task_patterns
        ])
        most_used = max(
            task_patterns,
            key=lambda p: p["metadata"]["usage_count"]
        ) if task_patterns else None

        return {
            "task_type": task_type,
            "total_patterns": total_patterns,
            "avg_success_rate": avg_success_rate,
            "most_used_pattern": most_used
        }
```

**价值**:
- Agent 可以从其他 Agent 的成功经验中学习
- 新 Agent 可以快速获得领域知识
- 整个系统的智能水平随着使用而提升

---

### 1.2 任务知识图谱

**创新描述**: 构建任务之间的关系网络，发现隐藏的依赖和模式

**实现方案**:

```python
# services/task_knowledge_graph.py

from typing import List, Dict, Any, Tuple
import networkx as nx

class TaskKnowledgeGraph:
    """任务知识图谱"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    def add_task_node(self, task_id: int, task_data: Dict[str, Any]):
        """添加任务节点"""
        self.graph.add_node(
            task_id,
            task_type=task_data["task_type"],
            description=task_data["description"],
            success=task_data.get("success", False),
            reward=task_data.get("reward", 0)
        )

    def add_similarity_edge(
        self,
        task1_id: int,
        task2_id: int,
        similarity: float
    ):
        """添加相似度边"""
        if similarity > 0.7:  # 只添加高相似度的边
            self.graph.add_edge(
                task1_id,
                task2_id,
                weight=similarity,
                relation="similar"
            )

    def add_dependency_edge(
        self,
        prerequisite_id: int,
        dependent_id: int
    ):
        """添加依赖边"""
        self.graph.add_edge(
            prerequisite_id,
            dependent_id,
            relation="prerequisite"
        )

    def find_task_clusters(self) -> List[List[int]]:
        """发现任务聚类"""
        # 使用社区发现算法
        communities = nx.community.louvain_communities(
            self.graph.to_undirected()
        )
        return [list(community) for community in communities]

    def recommend_next_tasks(
        self,
        completed_task_id: int,
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """推荐下一个任务"""
        if completed_task_id not in self.graph:
            return []

        # 1. 找到相似任务
        similar_tasks = []
        for neighbor in self.graph.neighbors(completed_task_id):
            edge_data = self.graph.get_edge_data(completed_task_id, neighbor)
            if edge_data.get("relation") == "similar":
                similar_tasks.append((neighbor, edge_data["weight"]))

        # 2. 找到依赖任务
        dependent_tasks = []
        for neighbor in self.graph.neighbors(completed_task_id):
            edge_data = self.graph.get_edge_data(completed_task_id, neighbor)
            if edge_data.get("relation") == "prerequisite":
                dependent_tasks.append((neighbor, 1.0))

        # 3. 合并并排序
        all_recommendations = similar_tasks + dependent_tasks
        all_recommendations.sort(key=lambda x: x[1], reverse=True)

        return all_recommendations[:top_k]

    def get_task_difficulty_score(self, task_id: int) -> float:
        """计算任务难度分数"""
        if task_id not in self.graph:
            return 0.5

        # 基于历史成功率计算
        node_data = self.graph.nodes[task_id]

        # 找到相似任务的成功率
        similar_tasks = [
            neighbor for neighbor in self.graph.neighbors(task_id)
            if self.graph.get_edge_data(task_id, neighbor).get("relation") == "similar"
        ]

        success_rates = []
        for similar_id in similar_tasks:
            similar_node = self.graph.nodes[similar_id]
            if similar_node.get("success") is not None:
                success_rates.append(1.0 if similar_node["success"] else 0.0)

        if success_rates:
            avg_success_rate = np.mean(success_rates)
            difficulty = 1.0 - avg_success_rate
            return difficulty
        else:
            return 0.5  # 默认中等难度

    def visualize_subgraph(
        self,
        center_task_id: int,
        depth: int = 2
    ) -> Dict[str, Any]:
        """可视化子图"""
        # 获取子图
        subgraph_nodes = nx.single_source_shortest_path_length(
            self.graph,
            center_task_id,
            cutoff=depth
        ).keys()

        subgraph = self.graph.subgraph(subgraph_nodes)

        # 转换为可视化格式
        nodes = []
        for node_id in subgraph.nodes():
            node_data = subgraph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "label": f"Task {node_id}",
                "type": node_data.get("task_type"),
                "success": node_data.get("success")
            })

        edges = []
        for source, target in subgraph.edges():
            edge_data = subgraph.get_edge_data(source, target)
            edges.append({
                "source": source,
                "target": target,
                "relation": edge_data.get("relation"),
                "weight": edge_data.get("weight", 1.0)
            })

        return {
            "nodes": nodes,
            "edges": edges
        }

    def get_critical_path(
        self,
        start_task_id: int,
        end_task_id: int
    ) -> List[int]:
        """获取关键路径"""
        try:
            path = nx.shortest_path(
                self.graph,
                start_task_id,
                end_task_id
            )
            return path
        except nx.NetworkXNoPath:
            return []

    def analyze_task_patterns(self, task_type: str) -> Dict[str, Any]:
        """分析任务模式"""
        # 过滤特定类型的任务
        type_tasks = [
            node_id for node_id in self.graph.nodes()
            if self.graph.nodes[node_id].get("task_type") == task_type
        ]

        if not type_tasks:
            return {}

        # 计算统计信息
        subgraph = self.graph.subgraph(type_tasks)

        return {
            "task_type": task_type,
            "total_tasks": len(type_tasks),
            "avg_degree": np.mean([
                subgraph.degree(node) for node in type_tasks
            ]),
            "density": nx.density(subgraph),
            "clusters": len(list(nx.connected_components(subgraph.to_undirected())))
        }
```

**价值**:
- 发现任务之间的隐藏关系
- 推荐相关任务
- 预测任务难度
- 优化任务执行顺序

---

### 1.3 技能树系统

**创新描述**: 为每个 Agent 构建技能树，追踪技能成长路径

**实现方案**:

```python
# services/skill_tree_service.py

class SkillTreeService:
    """技能树服务"""

    def __init__(self):
        self.memory_service = get_agent_memory_service()

    def build_skill_tree(self, agent_id: int) -> Dict[str, Any]:
        """构建 Agent 技能树"""
        # 1. 获取所有任务记忆
        memories = self.memory_service.vector_store.get_agent_memories(
            agent_id=agent_id,
            memory_type="task_execution"
        )

        # 2. 按任务类型分组
        task_types = {}
        for memory in memories:
            task_type = memory["metadata"]["task_type"]
            if task_type not in task_types:
                task_types[task_type] = {
                    "total": 0,
                    "success": 0,
                    "tasks": []
                }

            task_types[task_type]["total"] += 1
            if memory["metadata"]["success"]:
                task_types[task_type]["success"] += 1
            task_types[task_type]["tasks"].append(memory)

        # 3. 计算技能等级
        skills = {}
        for task_type, data in task_types.items():
            success_rate = data["success"] / data["total"]
            level = self._calculate_skill_level(data["total"], success_rate)

            skills[task_type] = {
                "level": level,
                "experience": data["total"],
                "success_rate": success_rate,
                "next_level_exp": self._exp_for_next_level(level)
            }

        return {
            "agent_id": agent_id,
            "skills": skills,
            "total_experience": sum(s["experience"] for s in skills.values()),
            "mastered_skills": [
                skill for skill, data in skills.items()
                if data["level"] >= 5
            ]
        }

    def _calculate_skill_level(
        self,
        experience: int,
        success_rate: float
    ) -> int:
        """计算技能等级"""
        # 基础等级（基于经验）
        base_level = min(int(experience / 10), 10)

        # 成功率调整
        if success_rate >= 0.9:
            bonus = 2
        elif success_rate >= 0.8:
            bonus = 1
        elif success_rate < 0.5:
            bonus = -1
        else:
            bonus = 0

        return max(1, min(base_level + bonus, 10))

    def _exp_for_next_level(self, current_level: int) -> int:
        """下一等级所需经验"""
        return (current_level + 1) * 10

    def recommend_skill_path(
        self,
        agent_id: int,
        target_skill: str
    ) -> List[str]:
        """推荐技能成长路径"""
        # 获取当前技能树
        skill_tree = self.build_skill_tree(agent_id)
        current_skills = skill_tree["skills"]

        # 定义技能依赖关系
        skill_dependencies = {
            "ADVANCED_CODE": ["CODE"],
            "ML_TRAINING": ["CODE", "DATA"],
            "SYSTEM_DESIGN": ["CODE", "RESEARCH"],
            "DATA_ENGINEERING": ["DATA", "COMPUTE"]
        }

        # 检查前置技能
        prerequisites = skill_dependencies.get(target_skill, [])
        missing_skills = []

        for prereq in prerequisites:
            if prereq not in current_skills or current_skills[prereq]["level"] < 3:
                missing_skills.append(prereq)

        # 构建推荐路径
        if missing_skills:
            return missing_skills + [target_skill]
        else:
            return [target_skill]

    def get_skill_recommendations(
        self,
        agent_id: int,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """获取技能推荐"""
        skill_tree = self.build_skill_tree(agent_id)
        current_skills = skill_tree["skills"]

        # 找到接近升级的技能
        near_levelup = []
        for skill, data in current_skills.items():
            exp_to_next = data["next_level_exp"] - data["experience"]
            if exp_to_next <= 5:  # 还需5次经验就升级
                near_levelup.append({
                    "skill": skill,
                    "current_level": data["level"],
                    "exp_needed": exp_to_next,
                    "reason": "即将升级"
                })

        # 找到可以学习的新技能
        all_skills = ["CODE", "DATA", "COMPUTE", "RESEARCH", "DESIGN", "WRITING"]
        new_skills = [
            skill for skill in all_skills
            if skill not in current_skills
        ]

        recommendations = near_levelup[:top_k]

        # 补充新技能推荐
        if len(recommendations) < top_k:
            for skill in new_skills[:top_k - len(recommendations)]:
                recommendations.append({
                    "skill": skill,
                    "current_level": 0,
                    "exp_needed": 10,
                    "reason": "拓展技能范围"
                })

        return recommendations
```

**价值**:
- 可视化 Agent 技能成长
- 推荐技能发展路径
- 激励 Agent 多样化发展
- 帮助任务匹配

---

### 1.4 声誉系统增强

**创新描述**: 基于记忆系统的多维度声誉计算

**实现方案**:

```python
# services/reputation_service.py

class EnhancedReputationService:
    """增强的声誉服务"""

    def calculate_reputation(self, agent_id: int) -> Dict[str, Any]:
        """计算多维度声誉"""
        # 1. 基础声誉（来自数据库）
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        base_reputation = agent.reputation

        # 2. 任务完成质量
        memories = self.memory_service.vector_store.get_agent_memories(
            agent_id=agent_id,
            memory_type="task_execution",
            limit=100
        )

        quality_score = self._calculate_quality_score(memories)

        # 3. 专业度评分
        skill_tree = self.skill_tree_service.build_skill_tree(agent_id)
        expertise_score = self._calculate_expertise_score(skill_tree)

        # 4. 协作贡献
        shared_patterns = self._get_shared_patterns(agent_id)
        collaboration_score = len(shared_patterns) * 10

        # 5. 综合声誉
        total_reputation = (
            base_reputation * 0.4 +
            quality_score * 0.3 +
            expertise_score * 0.2 +
            collaboration_score * 0.1
        )

        return {
            "agent_id": agent_id,
            "total_reputation": int(total_reputation),
            "breakdown": {
                "base": base_reputation,
                "quality": quality_score,
                "expertise": expertise_score,
                "collaboration": collaboration_score
            },
            "rank": self._calculate_rank(total_reputation)
        }

    def _calculate_quality_score(self, memories: List[Dict]) -> float:
        """计算质量分数"""
        if not memories:
            return 100.0

        # 成功率
        success_count = sum(
            1 for m in memories
            if m["metadata"]["success"]
        )
        success_rate = success_count / len(memories)

        # 平均执行时间（越快越好）
        execution_times = [
            m["metadata"].get("execution_time", 0)
            for m in memories
        ]
        avg_time = np.mean(execution_times) if execution_times else 0

        # 质量分数
        quality = success_rate * 100

        # 速度奖励
        if avg_time < 60:  # 1分钟内完成
            quality += 20
        elif avg_time < 300:  # 5分钟内完成
            quality += 10

        return min(quality, 200.0)

    def _calculate_expertise_score(self, skill_tree: Dict) -> float:
        """计算专业度分数"""
        skills = skill_tree["skills"]

        if not skills:
            return 50.0

        # 技能广度
        breadth = len(skills) * 10

        # 技能深度
        depth = sum(s["level"] for s in skills.values()) * 5

        # 精通技能数量
        mastered = len(skill_tree["mastered_skills"]) * 20

        return min(breadth + depth + mastered, 200.0)

    def _calculate_rank(self, reputation: float) -> str:
        """计算等级"""
        if reputation >= 500:
            return "Master"
        elif reputation >= 400:
            return "Expert"
        elif reputation >= 300:
            return "Advanced"
        elif reputation >= 200:
            return "Intermediate"
        else:
            return "Beginner"
```

**价值**:
- 更准确的 Agent 能力评估
- 多维度声誉体系
- 激励高质量工作
- 促进知识分享

---

## 2. 与 Evomap.ai 的差异化

| 维度 | Evomap.ai | Nautilus Memory System |
|------|-----------|------------------------|
| **应用场景** | 通用 AI 对话记忆 | 任务执行和 Agent 协作 |
| **记忆类型** | 对话历史、用户偏好 | 任务执行、技能成长、协作模式 |
| **协作性** | 单用户记忆 | 跨 Agent 协作记忆网络 |
| **知识图谱** | 概念关系 | 任务关系、技能依赖 |
| **激励机制** | 无 | 声誉系统、技能树、奖励 |
| **区块链集成** | 无 | 链上声誉、奖励分配 |

---

## 3. 技术优势总结

### 3.1 架构优势

1. **渐进式部署**: 基于现有 PostgreSQL，无需额外基础设施
2. **可扩展性**: 支持从 pgvector 平滑迁移到 Qdrant
3. **高性能**: 多级缓存 + 向量索引优化
4. **低成本**: 使用开源模型，本地部署

### 3.2 功能优势

1. **协作学习**: Agent 之间共享知识
2. **知识图谱**: 发现任务关系和模式
3. **技能系统**: 可视化成长路径
4. **智能推荐**: 基于历史的精准匹配

### 3.3 业务优势

1. **提高成功率**: 从历史经验学习
2. **优化分配**: 智能任务-Agent 匹配
3. **降低成本**: 减少失败和重试
4. **增强粘性**: 技能成长激励

---

## 4. 未来扩展方向

### 4.1 多模态记忆 (Phase 2)

支持图片、代码、数据等多模态记忆

```python
class MultimodalMemoryService:
    def remember_code_snippet(agent_id, code, language)
    def remember_data_pattern(agent_id, data_sample, schema)
    def remember_visual_result(agent_id, image, description)
```

### 4.2 联邦学习 (Phase 3)

跨 Nautilus 实例的联邦记忆学习

```python
class FederatedMemoryService:
    def sync_with_network(local_memories)
    def aggregate_global_patterns()
    def protect_privacy(memories)
```

### 4.3 自主进化 (Phase 4)

Agent 基于记忆自主优化策略

```python
class AutonomousEvolutionService:
    def analyze_failure_patterns(agent_id)
    def generate_improvement_plan(agent_id)
    def self_optimize_strategy(agent_id)
```

---

**总结**: Nautilus 记忆系统不仅借鉴了 Evomap.ai 的核心理念，更针对任务市场和 Agent 协作场景进行了深度创新，构建了独特的竞争优势。
