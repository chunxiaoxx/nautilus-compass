# Nautilus Control Plane (NCP) 架构重构草案
> 基于 Claude Code 与 OpenClaw 核心理念提炼

## 1. 核心理念：Gateway 仅作为控制平面
彻底废弃当前 `agent_executor.py` 中臃肿的单体执行逻辑。Nautilus 的核心网关将退化为一个极简的 **Control Plane (控制平面)**，仅负责状态机流转、A2A 消息路由和任务分发。

## 2. 架构三要素

### A. Gateway (控制平面)
- 纯路由逻辑，无业务代码
- 无状态消息代理
- 仅负责认证鉴权和路由

### B. Agent Grid (执行平面)
- 独立 Agent 进程
- 每个 Agent 拥有独立 Memory 和 Skills
- 按类型水平扩展

### C. Shared Knowledge Base (共享知识库)
- Protocol Schemas
- Shared Type Definitions
- Cross-Agent State Coordination

## 3. Agent 协作协议

### 握手流程
1. Agent 启动 → 向 Gateway 注册自身能力 (Capability Registration)
2. Gateway 维护一张 **Agent Capability Map** (AC Map)
3. 任务到达 → Gateway 查询 AC Map → 路由到合适的 Agent
4. Agent 处理 → 返回结果 → Gateway 清理会话状态

### A2A 协议
- Agent-to-Agent 消息通过 Gateway 转发
- 保留端到端加密选项
- 消息格式统一使用 JSON Schema

## 4. 实现优先级

1. **Phase 0**: 提取 Routing Logic → 独立 Router 模块
2. **Phase 1**: 定义 A2A Message Schema → JSON Schema Registry
3. **Phase 2**: 实现 Agent Registration Endpoint
4. **Phase 3**: 搭建 Agent Health Dashboard
5. **Phase 4**: 性能压测与调优

## 5. 参考资料
- Claude Code Agent Architecture
- OpenClaw Multi-Agent Coordination
- AWS Control Plane Best Practices
