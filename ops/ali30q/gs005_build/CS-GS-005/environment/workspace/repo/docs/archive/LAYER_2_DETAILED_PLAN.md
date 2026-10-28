# Layer 2 开发计划 - Orchestrator Engine

**层级**: Layer 2
**预计时间**: 21天（3周）
**组件**: Task Decomposer + Agent Matcher + Task Scheduler

---

## Phase 2.1: Task Decomposer（7天）

### Agent 7 - Decomposer开发专家

#### 任务目标
开发任务分解器，将复杂任务分解为子任务

#### 核心功能

**1. 任务理解模块**
```python
# orchestrator/task_decomposer.py

from typing import List, Dict, Any
import anthropic  # 或 openai

class TaskDecomposer:
    def __init__(self, llm_api_key: str):
        self.client = anthropic.Anthropic(api_key=llm_api_key)

    async def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """分析任务，理解需求"""
        prompt = f"""
        分析以下任务，提取关键信息：
        任务描述: {task_description}

        请提供：
        1. 任务类型
        2. 所需技能
        3. 预计复杂度
        4. 依赖关系
        5. 优先级
        """

        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_analysis(response.content)

    async def decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将任务分解为子任务"""
        prompt = f"""
        将以下任务分解为可执行的子任务：
        任务: {task['description']}
        类型: {task['type']}
        复杂度: {task['complexity']}

        要求：
        1. 每个子任务独立可执行
        2. 明确子任务之间的依赖关系
        3. 估算每个子任务的时间
        4. 指定所需的智能体能力
        """

        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_subtasks(response.content)

    def build_task_dag(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建任务依赖图（DAG）"""
        dag = {
            'nodes': {},
            'edges': []
        }

        for task in subtasks:
            dag['nodes'][task['id']] = task

            for dep in task.get('dependencies', []):
                dag['edges'].append({
                    'from': dep,
                    'to': task['id']
                })

        return dag
```

**2. 依赖分析模块**
```python
class DependencyAnalyzer:
    def analyze_dependencies(self, subtasks: List[Dict]) -> Dict[str, List[str]]:
        """分析任务依赖关系"""
        dependencies = {}

        for task in subtasks:
            task_id = task['id']
            deps = []

            # 分析输入输出依赖
            for other_task in subtasks:
                if other_task['id'] == task_id:
                    continue

                if self._has_dependency(task, other_task):
                    deps.append(other_task['id'])

            dependencies[task_id] = deps

        return dependencies

    def _has_dependency(self, task_a: Dict, task_b: Dict) -> bool:
        """判断task_a是否依赖task_b"""
        # 检查输出是否是输入
        task_b_outputs = set(task_b.get('outputs', []))
        task_a_inputs = set(task_a.get('inputs', []))

        return bool(task_b_outputs & task_a_inputs)

    def topological_sort(self, dag: Dict) -> List[str]:
        """拓扑排序，确定执行顺序"""
        in_degree = {node: 0 for node in dag['nodes']}

        for edge in dag['edges']:
            in_degree[edge['to']] += 1

        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for edge in dag['edges']:
                if edge['from'] == node:
                    in_degree[edge['to']] -= 1
                    if in_degree[edge['to']] == 0:
                        queue.append(edge['to'])

        return result
```

**3. 优先级排序模块**
```python
class PriorityManager:
    def calculate_priority(self, task: Dict) -> float:
        """计算任务优先级"""
        factors = {
            'urgency': task.get('urgency', 0.5),
            'importance': task.get('importance', 0.5),
            'complexity': 1 - task.get('complexity', 0.5),
            'dependencies': len(task.get('dependencies', [])) / 10
        }

        weights = {
            'urgency': 0.4,
            'importance': 0.3,
            'complexity': 0.2,
            'dependencies': 0.1
        }

        priority = sum(factors[k] * weights[k] for k in factors)
        return priority

    def sort_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """按优先级排序任务"""
        for task in tasks:
            task['priority'] = self.calculate_priority(task)

        return sorted(tasks, key=lambda x: x['priority'], reverse=True)
```

#### 测试要求
- 30+ 单元测试
- 10+ 集成测试
- 80%+ 覆盖率

---

### Agent 8 - Decomposer测试专家

#### 测试场景

**1. 简单任务分解**
```python
async def test_simple_task_decomposition():
    decomposer = TaskDecomposer(api_key="test-key")

    task = {
        'description': '创建一个用户注册功能',
        'type': 'feature',
        'complexity': 'medium'
    }

    subtasks = await decomposer.decompose_task(task)

    assert len(subtasks) >= 3
    assert any('数据库' in t['description'] for t in subtasks)
    assert any('API' in t['description'] for t in subtasks)
    assert any('测试' in t['description'] for t in subtasks)
```

**2. 复杂任务分解**
```python
async def test_complex_task_decomposition():
    task = {
        'description': '构建一个完整的电商系统',
        'type': 'project',
        'complexity': 'high'
    }

    subtasks = await decomposer.decompose_task(task)

    assert len(subtasks) >= 10
    # 验证有前端、后端、数据库、支付等子任务
```

**3. 依赖关系测试**
```python
def test_dependency_analysis():
    subtasks = [
        {'id': '1', 'outputs': ['database_schema']},
        {'id': '2', 'inputs': ['database_schema'], 'outputs': ['api']},
        {'id': '3', 'inputs': ['api'], 'outputs': ['frontend']}
    ]

    analyzer = DependencyAnalyzer()
    deps = analyzer.analyze_dependencies(subtasks)

    assert '1' in deps['2']
    assert '2' in deps['3']
```

---

### Agent 9 - 文档专家

#### 文档内容

**1. API文档**
- TaskDecomposer类文档
- 所有方法的参数和返回值
- 使用示例

**2. 架构文档**
- 组件设计
- 数据流图
- 集成方式

**3. 使用指南**
- 快速开始
- 配置说明
- 最佳实践

---

## Phase 2.2: Agent Matcher（7天）

### Agent 10 - Matcher开发专家

#### 核心功能

**1. 能力评估模块**
```python
# orchestrator/agent_matcher.py

class AgentMatcher:
    def __init__(self):
        self.agents = {}  # agent_id -> capabilities

    def register_agent(self, agent_id: str, capabilities: Dict[str, Any]):
        """注册智能体及其能力"""
        self.agents[agent_id] = {
            'id': agent_id,
            'capabilities': capabilities,
            'performance': {
                'success_rate': 1.0,
                'avg_time': 0,
                'completed_tasks': 0
            },
            'load': 0,
            'status': 'available'
        }

    def match_agent(self, task: Dict[str, Any]) -> str:
        """为任务匹配最合适的智能体"""
        required_skills = task.get('required_skills', [])
        candidates = []

        for agent_id, agent in self.agents.items():
            if agent['status'] != 'available':
                continue

            score = self._calculate_match_score(agent, task)
            if score > 0.5:  # 阈值
                candidates.append((agent_id, score))

        if not candidates:
            return None

        # 按分数排序，选择最佳
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _calculate_match_score(self, agent: Dict, task: Dict) -> float:
        """计算匹配分数"""
        # 技能匹配
        skill_score = self._skill_match_score(
            agent['capabilities'].get('skills', []),
            task.get('required_skills', [])
        )

        # 性能评分
        performance_score = agent['performance']['success_rate']

        # 负载评分
        load_score = 1 - (agent['load'] / 10)

        # 综合评分
        score = (
            skill_score * 0.5 +
            performance_score * 0.3 +
            load_score * 0.2
        )

        return score

    def _skill_match_score(self, agent_skills: List[str],
                          required_skills: List[str]) -> float:
        """计算技能匹配度"""
        if not required_skills:
            return 1.0

        matched = sum(1 for skill in required_skills if skill in agent_skills)
        return matched / len(required_skills)
```

**2. 负载均衡模块**
```python
class LoadBalancer:
    def balance_load(self, agents: Dict[str, Dict]) -> str:
        """负载均衡选择智能体"""
        available = [
            (aid, agent) for aid, agent in agents.items()
            if agent['status'] == 'available'
        ]

        if not available:
            return None

        # 选择负载最低的
        return min(available, key=lambda x: x[1]['load'])[0]

    def update_load(self, agent_id: str, delta: int):
        """更新智能体负载"""
        if agent_id in self.agents:
            self.agents[agent_id]['load'] += delta
```

**3. 信誉系统模块**
```python
class ReputationSystem:
    def update_reputation(self, agent_id: str, task_result: Dict):
        """更新智能体信誉"""
        agent = self.agents.get(agent_id)
        if not agent:
            return

        perf = agent['performance']

        # 更新成功率
        total = perf['completed_tasks']
        success = task_result['success']

        perf['success_rate'] = (
            (perf['success_rate'] * total + (1 if success else 0)) /
            (total + 1)
        )

        # 更新平均时间
        perf['avg_time'] = (
            (perf['avg_time'] * total + task_result['duration']) /
            (total + 1)
        )

        perf['completed_tasks'] += 1
```

---

## Phase 2.3: Task Scheduler（7天）

### Agent 13 - Scheduler开发专家

#### 核心功能

**1. 任务队列管理**
```python
# orchestrator/task_scheduler.py

import asyncio
from queue import PriorityQueue

class TaskScheduler:
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = {}

    async def schedule_task(self, task: Dict[str, Any]):
        """调度任务"""
        priority = task.get('priority', 0.5)
        self.task_queue.put((-priority, task))  # 负数实现最大堆

    async def execute_tasks(self):
        """执行任务"""
        while True:
            if self.task_queue.empty():
                await asyncio.sleep(1)
                continue

            _, task = self.task_queue.get()

            # 检查依赖
            if not self._dependencies_met(task):
                self.task_queue.put((task['priority'], task))
                continue

            # 匹配智能体
            agent_id = await self.matcher.match_agent(task)
            if not agent_id:
                self.task_queue.put((task['priority'], task))
                await asyncio.sleep(1)
                continue

            # 执行任务
            asyncio.create_task(self._execute_task(task, agent_id))

    async def _execute_task(self, task: Dict, agent_id: str):
        """执行单个任务"""
        task_id = task['id']
        self.running_tasks[task_id] = {
            'task': task,
            'agent': agent_id,
            'start_time': time.time()
        }

        try:
            # 发送任务给智能体
            result = await self._send_to_agent(task, agent_id)

            # 更新状态
            self.completed_tasks[task_id] = {
                'task': task,
                'result': result,
                'duration': time.time() - self.running_tasks[task_id]['start_time']
            }

        except Exception as e:
            # 处理失败
            await self._handle_failure(task, agent_id, e)

        finally:
            del self.running_tasks[task_id]
```

**2. 失败重试模块**
```python
class RetryManager:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.retry_counts = {}

    async def handle_failure(self, task: Dict, error: Exception):
        """处理任务失败"""
        task_id = task['id']
        retry_count = self.retry_counts.get(task_id, 0)

        if retry_count < self.max_retries:
            # 重试
            self.retry_counts[task_id] = retry_count + 1
            await asyncio.sleep(2 ** retry_count)  # 指数退避
            await self.scheduler.schedule_task(task)
        else:
            # 标记为失败
            await self._mark_as_failed(task, error)
```

**3. 结果聚合模块**
```python
class ResultAggregator:
    async def aggregate_results(self, task_id: str) -> Dict[str, Any]:
        """聚合子任务结果"""
        subtasks = self.get_subtasks(task_id)
        results = []

        for subtask_id in subtasks:
            result = await self.wait_for_result(subtask_id)
            results.append(result)

        return {
            'task_id': task_id,
            'subtask_results': results,
            'success': all(r['success'] for r in results),
            'aggregated_output': self._merge_outputs(results)
        }
```

---

## 验收标准（超高标准）

### Task Decomposer
- ✅ 可以分解各种复杂度的任务
- ✅ 依赖关系分析准确
- ✅ 优先级排序合理
- ✅ 80%+ 测试覆盖率

### Agent Matcher
- ✅ 匹配准确率 > 90%
- ✅ 负载均衡有效
- ✅ 信誉系统可靠
- ✅ 80%+ 测试覆盖率

### Task Scheduler
- ✅ 任务调度高效
- ✅ 失败重试可靠
- ✅ 结果聚合正确
- ✅ 80%+ 测试覆盖率

### 整体集成
- ✅ 三个组件无缝集成
- ✅ 端到端测试通过
- ✅ 性能达标
- ✅ 文档完整

---

**准备就绪，等待Layer 1完成后立即启动！**
