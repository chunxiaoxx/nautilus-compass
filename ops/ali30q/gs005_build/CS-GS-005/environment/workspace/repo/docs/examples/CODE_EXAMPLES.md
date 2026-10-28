# Nautilus 代码示例

## 示例 1: 基础使用

```python
from nautilus import Nautilus

# 初始化
nautilus = Nautilus()

# 创建任务
task = nautilus.create_task(
    name="天气App",
    description="写一个Python天气App",
    agents=["python-dev", "ui-designer"]
)

# 执行
result = task.run()

# 获取结果
print(result.files)
print(result.report)
```

---

## 示例 2: 自定义 Agent

```python
from nautilus import Agent

# 创建自定义 Agent
my_agent = Agent(
    name="Blog Writer",
    description="专业博客写手",
    capabilities=["writing", "seo"],
    system_prompt="""你是专业博客写手。
    擅长技术文章，
    风格深入浅出。"""
)

# 注册 Agent
nautilus.register_agent(my_agent)

# 使用
task = nautilus.create_task("写一篇关于AI的文章")
```

---

## 示例 3: 多 Agent 协作

```python
from nautilus import Nautilus, Task

nautilus = Nautilus()

# 创建复杂任务
task = Task("发布新产品")

# 添加 Agent 团队
task.add_agent("market-researcher")
task.add_agent("content-writer")
task.add_agent("designer")
task.add_agent("social-media-manager")

# 设置依赖
task.set_dependencies({
    "content-writer": ["market-researcher"],
    "designer": ["market-researcher"],
    "social-media-manager": ["content-writer", "designer"]
})

# 执行
result = task.run()

# 结果包含
print(result.market_report)   # 市场分析
print(result.content)         # 文案
print(result.designs)         # 设计稿
print(result.social_posts)    # 社交媒体内容
```

---

## 示例 4: 使用 Epiplexity 评估

```python
from nautilus import Nautilus
from nautilus.evaluation import Epiplexity

nautilus = Nautilus()
evaluator = Epiplexity()

# 创建任务
task = nautilus.create_task("分析数据并可视化")

# 执行
result = task.run()

# 评估 Agent 表现
for agent_result in result.agent_results:
    score = evaluator.evaluate(
        agent=agent_result.agent,
        task=task,
        output=agent_result.output
    )
    
    print(f"Agent: {agent_result.agent.name}")
    print(f"Epiplexity: {score.epiplexity}")
    print(f"Knowledge Creation: {score.knowledge_creation}")
    print(f"Learning: {score.learning}")
    print(f"Emergence: {score.emergence}")
```

---

## 示例 5: API 调用

```bash
# 创建任务
curl -X POST http://localhost:18789/api/tasks \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "天气App",
    "description": "写一个天气App",
    "agents": ["python-dev"],
    "requirements": {
      "api": "使用天气API",
      "ui": "简洁UI",
      "features": ["当前天气", "7天预报"]
    }
  }'

# 获取结果
curl http://localhost:18789/api/tasks/{task_id}

# 评估
curl http://localhost:18789/api/evaluations/{task_id}
```

---

## 示例 6: 插件开发

```python
from nautilus import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def on_task_created(self, task):
        print(f"新任务: {task.name}")
    
    def on_agent_result(self, agent, result):
        print(f"Agent {agent.name} 完成")
    
    def on_task_complete(self, task):
        print(f"任务完成: {task.name}")

# 注册插件
nautilus.register_plugin(MyPlugin())
```

---

*更多示例见 GitHub: github.com/chunxiaoxx/nautilus-core*
