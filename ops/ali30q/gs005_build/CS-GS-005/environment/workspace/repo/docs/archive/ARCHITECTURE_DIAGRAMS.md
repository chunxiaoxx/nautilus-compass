# Nautilus Trinity Engine 架构图

**版本**: 1.0.0
**创建时间**: 2026-02-24
**作者**: Nautilus开发团队

---

## 📐 目录

1. [系统总体架构图](#1-系统总体架构图)
2. [Nexus Protocol 消息流转时序图](#2-nexus-protocol-消息流转时序图)
3. [智能体状态机图](#3-智能体状态机图)
4. [部署架构图](#4-部署架构图)
5. [数据流图](#5-数据流图)
6. [组件交互图](#6-组件交互图)

---

## 1. 系统总体架构图

### 1.1 Trinity Engine 三层架构

```mermaid
graph TB
    subgraph "Nautilus Trinity Engine (NTE)"
        subgraph "Layer 1: Nexus Protocol (NP)"
            NP[Nexus Protocol<br/>A2A通信层]
            NS[Nexus Server<br/>消息路由]
            NC[Nexus Client<br/>智能体客户端]
        end

        subgraph "Layer 2: Orchestrator Engine (OE)"
            TD[Task Decomposer<br/>任务分解器]
            AM[Agent Matcher<br/>智能匹配器]
            TS[Task Scheduler<br/>任务调度器]
        end

        subgraph "Layer 3: Memory Chain (MC)"
            STM[Short-term Memory<br/>Redis]
            LTM[Long-term Memory<br/>PostgreSQL]
            BC[Blockchain<br/>POW共识]
        end
    end

    subgraph "External Systems"
        LLM[LLM APIs<br/>Claude/GPT]
        USER[User Interface<br/>Web/API]
        AGENTS[Agent Pool<br/>智能体池]
    end

    USER --> OE
    OE --> NP
    OE --> LLM
    NP --> NS
    NS --> NC
    NC --> AGENTS
    OE --> MC
    MC --> BC

    style NP fill:#e1f5ff
    style OE fill:#fff4e1
    style MC fill:#f0e1ff
```

### 1.2 核心组件关系图

```mermaid
graph LR
    subgraph "Frontend"
        UI[Web UI]
        API[REST API]
    end

    subgraph "Backend Core"
        AUTH[认证服务]
        TASK[任务服务]
        AGENT[智能体服务]
    end

    subgraph "Nexus Protocol"
        SERVER[Nexus Server]
        ROUTER[Message Router]
    end

    subgraph "Orchestrator"
        DECOMP[Decomposer]
        MATCH[Matcher]
        SCHED[Scheduler]
    end

    subgraph "Storage"
        REDIS[(Redis)]
        PG[(PostgreSQL)]
        CHAIN[(Blockchain)]
    end

    UI --> API
    API --> AUTH
    API --> TASK
    TASK --> DECOMP
    DECOMP --> MATCH
    MATCH --> SCHED
    SCHED --> SERVER
    SERVER --> ROUTER
    ROUTER --> AGENT

    TASK --> REDIS
    TASK --> PG
    AGENT --> CHAIN
```

---

## 2. Nexus Protocol 消息流转时序图

### 2.1 A2A协作请求流程

```mermaid
sequenceDiagram
    participant AgentA as Agent A<br/>(请求方)
    participant Server as Nexus Server<br/>(路由中心)
    participant AgentB as Agent B<br/>(执行方)

    Note over AgentA,AgentB: 1. 连接和注册阶段
    AgentA->>Server: connect()
    Server-->>AgentA: connected
    AgentA->>Server: HELLO(agent_id, capabilities)
    Server-->>AgentA: HELLO_ACK(online_agents)

    AgentB->>Server: connect()
    Server-->>AgentB: connected
    AgentB->>Server: HELLO(agent_id, capabilities)
    Server-->>AgentB: HELLO_ACK(online_agents)
    Server-->>AgentA: agent_status(AgentB, online)

    Note over AgentA,AgentB: 2. 协作请求阶段
    AgentA->>Server: REQUEST(task_id, description, reward)
    Server->>AgentB: REQUEST(from AgentA)

    Note over AgentB: 评估任务<br/>决定是否接受

    AgentB->>Server: ACCEPT(request_id, estimated_time)
    Server->>AgentA: ACCEPT(session_id)

    Note over AgentA,AgentB: 3. 任务执行阶段
    loop 任务执行中
        AgentB->>Server: PROGRESS(session_id, 30%)
        Server->>AgentA: PROGRESS(30%)
        AgentB->>Server: PROGRESS(session_id, 60%)
        Server->>AgentA: PROGRESS(60%)
        AgentB->>Server: PROGRESS(session_id, 90%)
        Server->>AgentA: PROGRESS(90%)
    end

    Note over AgentA,AgentB: 4. 任务完成阶段
    AgentB->>Server: COMPLETE(session_id, result)
    Server->>AgentA: COMPLETE(result)

    Note over AgentA: 验证结果<br/>确认完成
```

### 2.2 知识共享流程

```mermaid
sequenceDiagram
    participant Expert as Expert Agent<br/>(专家智能体)
    participant Server as Nexus Server
    participant Learner1 as Learner Agent 1
    participant Learner2 as Learner Agent 2

    Note over Expert,Learner2: 智能体已连接并注册

    Expert->>Server: SHARE(to_agents=[L1,L2], knowledge)

    par 并行广播
        Server->>Learner1: SHARE(from Expert, knowledge)
        Server->>Learner2: SHARE(from Expert, knowledge)
    end

    Note over Learner1: 接收并学习<br/>更新知识库
    Note over Learner2: 接收并学习<br/>更新知识库

    Learner1-->>Server: ACK(received)
    Learner2-->>Server: ACK(received)

    Server-->>Expert: SHARE_ACK(2 agents received)
```

### 2.3 任务拒绝和替代方案流程

```mermaid
sequenceDiagram
    participant AgentA as Agent A
    participant Server as Nexus Server
    participant AgentB as Agent B
    participant AgentC as Agent C

    AgentA->>Server: REQUEST(task, to=AgentB)
    Server->>AgentB: REQUEST(from AgentA)

    Note over AgentB: 评估后<br/>无法接受

    AgentB->>Server: REJECT(reason, alternative=AgentC)
    Server->>AgentA: REJECT(reason, alternative=AgentC)

    Note over AgentA: 根据建议<br/>重新发送请求

    AgentA->>Server: REQUEST(task, to=AgentC)
    Server->>AgentC: REQUEST(from AgentA)

    AgentC->>Server: ACCEPT(request_id)
    Server->>AgentA: ACCEPT(session_id)
```

---

## 3. 智能体状态机图

### 3.1 智能体生命周期状态

```mermaid
stateDiagram-v2
    [*] --> Offline: 创建智能体

    Offline --> Connecting: connect()
    Connecting --> Online: HELLO成功
    Connecting --> Offline: 连接失败

    Online --> Idle: 注册完成

    Idle --> Busy: 接受任务
    Idle --> Offline: disconnect()

    Busy --> Working: 开始执行
    Busy --> Idle: 拒绝任务

    Working --> Busy: 任务完成
    Working --> Error: 执行失败

    Error --> Idle: 错误恢复
    Error --> Offline: 严重错误

    Offline --> [*]: 销毁智能体

    note right of Online
        可以接收消息
        可以查询其他智能体
    end note

    note right of Working
        发送进度更新
        执行任务逻辑
    end note
```

### 3.2 任务状态机

```mermaid
stateDiagram-v2
    [*] --> Created: 创建任务

    Created --> Decomposed: 任务分解
    Decomposed --> Matching: 智能体匹配

    Matching --> Pending: 找到匹配
    Matching --> Failed: 无匹配智能体

    Pending --> Requested: 发送REQUEST

    Requested --> Accepted: 收到ACCEPT
    Requested --> Rejected: 收到REJECT
    Requested --> Timeout: 超时无响应

    Rejected --> Matching: 重新匹配
    Timeout --> Matching: 重新匹配

    Accepted --> InProgress: 开始执行

    InProgress --> InProgress: 收到PROGRESS
    InProgress --> Completed: 收到COMPLETE(success)
    InProgress --> Failed: 收到COMPLETE(error)
    InProgress --> Timeout: 执行超时

    Completed --> [*]: 任务结束
    Failed --> [*]: 任务结束

    note right of InProgress
        持续监控进度
        更新状态到数据库
    end note
```

---

## 4. 部署架构图

### 4.1 生产环境部署

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx<br/>负载均衡]
    end

    subgraph "Application Layer"
        API1[API Server 1<br/>FastAPI]
        API2[API Server 2<br/>FastAPI]
        API3[API Server 3<br/>FastAPI]
    end

    subgraph "Nexus Layer"
        NS1[Nexus Server 1<br/>WebSocket]
        NS2[Nexus Server 2<br/>WebSocket]
    end

    subgraph "Orchestrator Layer"
        OE1[Orchestrator 1<br/>Task Engine]
        OE2[Orchestrator 2<br/>Task Engine]
    end

    subgraph "Data Layer"
        REDIS_M[(Redis Master)]
        REDIS_S1[(Redis Slave 1)]
        REDIS_S2[(Redis Slave 2)]

        PG_M[(PostgreSQL Master)]
        PG_S1[(PostgreSQL Slave 1)]
        PG_S2[(PostgreSQL Slave 2)]
    end

    subgraph "Agent Pool"
        A1[Agent 1]
        A2[Agent 2]
        A3[Agent N]
    end

    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> NS1
    API2 --> NS1
    API3 --> NS2

    API1 --> OE1
    API2 --> OE2
    API3 --> OE1

    NS1 --> A1
    NS1 --> A2
    NS2 --> A3

    OE1 --> REDIS_M
    OE2 --> REDIS_M
    REDIS_M --> REDIS_S1
    REDIS_M --> REDIS_S2

    OE1 --> PG_M
    OE2 --> PG_M
    PG_M --> PG_S1
    PG_M --> PG_S2

    style LB fill:#ff9999
    style REDIS_M fill:#99ccff
    style PG_M fill:#99ff99
```

### 4.2 开发环境部署

```mermaid
graph TB
    subgraph "Developer Machine"
        DEV[开发环境<br/>localhost]

        subgraph "Docker Compose"
            API[API Server<br/>:8000]
            NS[Nexus Server<br/>:8001]
            REDIS[(Redis<br/>:6379)]
            PG[(PostgreSQL<br/>:5432)]
        end

        subgraph "Local Agents"
            A1[Test Agent 1]
            A2[Test Agent 2]
        end
    end

    DEV --> API
    API --> NS
    API --> REDIS
    API --> PG
    NS --> A1
    NS --> A2

    style DEV fill:#ffffcc
```

---

## 5. 数据流图

### 5.1 任务处理数据流

```mermaid
graph LR
    subgraph "Input"
        USER[用户请求]
    end

    subgraph "Processing"
        PARSE[解析任务]
        DECOMP[任务分解]
        MATCH[智能体匹配]
        ROUTE[消息路由]
        EXEC[任务执行]
    end

    subgraph "Storage"
        CACHE[(缓存<br/>Redis)]
        DB[(数据库<br/>PostgreSQL)]
        CHAIN[(区块链)]
    end

    subgraph "Output"
        RESULT[执行结果]
    end

    USER --> PARSE
    PARSE --> DECOMP
    DECOMP --> CACHE
    DECOMP --> MATCH
    MATCH --> CACHE
    MATCH --> ROUTE
    ROUTE --> EXEC
    EXEC --> DB
    EXEC --> RESULT
    RESULT --> CHAIN

    style CACHE fill:#e1f5ff
    style DB fill:#f0e1ff
    style CHAIN fill:#fff4e1
```

### 5.2 消息流转数据流

```mermaid
graph TB
    A[Agent A<br/>发送消息] --> V[消息验证]
    V --> S[消息签名]
    S --> Q[消息队列]
    Q --> R[路由决策]

    R --> U{路由类型}
    U -->|单播| T1[目标Agent]
    U -->|广播| T2[所有在线Agent]
    U -->|组播| T3[特定组Agent]

    T1 --> P1[持久化]
    T2 --> P1
    T3 --> P1

    P1 --> L[日志记录]
    L --> M[监控指标]
```

---

## 6. 组件交互图

### 6.1 Orchestrator Engine 内部交互

```mermaid
graph TB
    subgraph "Orchestrator Engine"
        INPUT[任务输入]

        subgraph "Task Decomposer"
            PARSE[解析器]
            LLM[LLM调用]
            SPLIT[分解器]
        end

        subgraph "Agent Matcher"
            QUERY[能力查询]
            SCORE[评分算法]
            SELECT[选择器]
        end

        subgraph "Task Scheduler"
            QUEUE[任务队列]
            DISPATCH[分发器]
            MONITOR[监控器]
        end

        OUTPUT[任务分配]
    end

    INPUT --> PARSE
    PARSE --> LLM
    LLM --> SPLIT
    SPLIT --> QUERY
    QUERY --> SCORE
    SCORE --> SELECT
    SELECT --> QUEUE
    QUEUE --> DISPATCH
    DISPATCH --> MONITOR
    MONITOR --> OUTPUT

    style LLM fill:#ffe1e1
```

### 6.2 Memory Chain 交互

```mermaid
graph LR
    subgraph "Memory Chain"
        subgraph "Short-term"
            WRITE[写入操作]
            READ[读取操作]
            REDIS[(Redis)]
        end

        subgraph "Long-term"
            ARCHIVE[归档操作]
            QUERY[查询操作]
            PG[(PostgreSQL)]
        end

        subgraph "Blockchain"
            HASH[哈希计算]
            POW[POW共识]
            CHAIN[(区块链)]
        end
    end

    WRITE --> REDIS
    READ --> REDIS
    REDIS -->|TTL过期| ARCHIVE
    ARCHIVE --> PG
    QUERY --> PG
    PG -->|重要数据| HASH
    HASH --> POW
    POW --> CHAIN
```

---

## 📊 架构特点总结

### 优势
1. ✅ **模块化设计**: 三层架构清晰分离
2. ✅ **可扩展性**: 每层可独立扩展
3. ✅ **高可用性**: 支持多实例部署
4. ✅ **异步通信**: WebSocket实时通信
5. ✅ **数据持久化**: 多层存储策略

### 技术栈
- **通信层**: Socket.IO, WebSocket
- **应用层**: FastAPI, Python 3.11+
- **存储层**: Redis, PostgreSQL, Blockchain
- **AI层**: Claude API, OpenAI API
- **部署**: Docker, Kubernetes

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-24
**维护人**: Nautilus开发团队
