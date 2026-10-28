# 🚀 Super Agent 快速参考指南

**版本**: 1.0 | **日期**: 2026-03-04

---

## 📖 文档导航

### 核心文档（按阅读顺序）

1. **SUPER_AGENT_FINAL_SUMMARY.md** ⭐ 从这里开始
   - 执行摘要和总体概览
   - 三大项目对比
   - 推荐方案和实施路线图
   - 阅读时间: 10分钟

2. **SUPER_AGENT_INTEGRATION_PLAN.md** (Part 1)
   - 方案1: EvoMap作为能力继承层
   - A2A协议客户端实现
   - 增强的Agent执行器
   - 阅读时间: 20分钟

3. **SUPER_AGENT_INTEGRATION_PLAN_PART2.md** (Part 2)
   - 方案2: Automaton作为生存层
   - 方案3: 三层架构整合
   - 方案4: 渐进式集成路线图
   - 阅读时间: 25分钟

4. **SUPER_AGENT_INTEGRATION_PLAN_PART3.md** (Part 3)
   - 完整实施示例
   - 配置文件和数据库Schema
   - 测试策略和监控方案
   - 阅读时间: 30分钟

### 辅助文档

5. **AUTOMATON_INTEGRATION_PLAN.md**
   - Automaton项目详细分析
   - 三种集成方式
   - 阅读时间: 15分钟

6. **NAUTILUS_COMPREHENSIVE_ANALYSIS_2026-03-04.md**
   - Nautilus完整分析报告
   - 代码审查和安全审计
   - 阅读时间: 45分钟

---

## 🎯 核心概念速查

### Super Agent公式

```
Super Agent = EvoMap(记忆DNA) + Nautilus(执行引擎) + Automaton(生存机制)
```

### 三层架构

```
Layer 1: EvoMap (记忆DNA层)
  ↓ A2A协议
Layer 2: Nautilus (执行引擎层)
  ↓ Integration API
Layer 3: Automaton (生存机制层)
```

### 关键组件

| 组件 | 功能 | 文件位置 |
|------|------|------|
| A2AClient | EvoMap协议客户端 | `evomap_integration/a2a_client.py` |
| EnhancedAgentExecutor | 增强的执行器 | `orchestrator/enhanced_executor.py` |
| AutomatonFinancialSystem | 财务系统 | `automaton_integration/financial_system.py` |
| AutomatonPolicyEngine | 策略引擎 | `automaton_integration/policy_engine.py` |
| HeartbeatDaemon | 心跳守护进程 | `automaton_integration/heartbeat.py` |
| SuperAgent | 统一Agent类 | `super_agent/agent.py` |

---

## 📋 实施检查清单

### Phase 1: 基础集成 (2周)

- [ ] 克隆Automaton仓库到本地
- [ ] 研究A2A协议规范
- [ ] 实现A2AClient类
  - [ ] fetch_capsule方法
  - [ ] publish_capsule方法
  - [ ] report_usage方法
- [ ] 实现EnhancedAgentExecutor
  - [ ] _extract_signals方法
  - [ ] _apply_capsule_strategy方法
  - [ ] execute_task_with_evolution方法
- [ ] 编写单元测试
  - [ ] test_a2a_client.py
  - [ ] test_enhanced_executor.py
- [ ] 集成测试
- [ ] 文档更新

**验收标准**:
- ✅ 可以从EvoMap获取Capsule
- ✅ 可以发布Capsule到EvoMap
- ✅ 测试覆盖率 > 80%

### Phase 2: 财务系统 (2周)

- [ ] 创建Ethereum测试钱包
- [ ] 获取测试USDC
- [ ] 实现AutomatonFinancialSystem
  - [ ] check_survival_tier方法
  - [ ] auto_topup_if_needed方法
  - [ ] _get_conway_credits方法
  - [ ] _get_usdc_balance方法
  - [ ] _topup_credits方法
- [ ] 实现SurvivalMonitor
  - [ ] start_monitoring方法
  - [ ] _send_distress_signal方法
  - [ ] _downgrade_model方法
- [ ] 实现x402支付协议
- [ ] 编写单元测试
  - [ ] test_financial_system.py
  - [ ] test_survival_monitor.py
- [ ] 集成测试
- [ ] 文档更新

**验收标准**:
- ✅ 生存层级正确切换
- ✅ 自动充值正常工作
- ✅ 测试覆盖率 > 80%

### Phase 3: 策略引擎 (1周)

- [ ] 实现AutomatonPolicyEngine
  - [ ] evaluate_tool_call方法
  - [ ] _check_forbidden_commands方法
  - [ ] _check_financial_limits方法
  - [ ] _check_path_protection方法
  - [ ] _check_rate_limits方法
- [ ] 集成到工具调用流程
- [ ] 编写单元测试
  - [ ] test_policy_engine.py
- [ ] 安全测试
- [ ] 文档更新

**验收标准**:
- ✅ 危险命令被拦截
- ✅ 财务限制生效
- ✅ 路径保护生效
- ✅ 测试覆盖率 > 80%

### Phase 4: 心跳系统 (1周)

- [ ] 实现HeartbeatDaemon
  - [ ] start方法
  - [ ] stop方法
  - [ ] _should_run_task方法
- [ ] 实现默认心跳任务
  - [ ] _check_credits
  - [ ] _check_usdc
  - [ ] _health_check
  - [ ] _cleanup_old_data
- [ ] 集成到Agent生命周期
- [ ] 编写单元测试
  - [ ] test_heartbeat.py
- [ ] 集成测试
- [ ] 文档更新

**验收标准**:
- ✅ 心跳任务按时执行
- ✅ 余额自动监控
- ✅ 测试覆盖率 > 80%

### Phase 5: Super Agent (2周)

- [ ] 实现SuperAgent类
  - [ ] start方法
  - [ ] stop方法
  - [ ] execute_task方法
  - [ ] _monitor_survival方法
- [ ] 统一配置管理
  - [ ] super_agent.yml
  - [ ] 环境变量
- [ ] 数据库Schema扩展
  - [ ] evomap_capsules表
  - [ ] evomap_usage_logs表
  - [ ] automaton_transactions表
  - [ ] automaton_policy_decisions表
  - [ ] automaton_heartbeat_logs表
  - [ ] automaton_soul_history表
- [ ] 完整的E2E测试
  - [ ] test_super_agent.py
  - [ ] test_evomap_integration.py
- [ ] 性能测试
  - [ ] test_performance.py
- [ ] 监控和告警
  - [ ] Prometheus指标
  - [ ] Grafana仪表板
- [ ] 生产部署
  - [ ] Docker镜像
  - [ ] Kubernetes配置
  - [ ] CI/CD流程
- [ ] 文档完善
  - [ ] 用户手册
  - [ ] API文档
  - [ ] 运维手册

**验收标准**:
- ✅ 完整的E2E流程正常
- ✅ API响应时间 < 200ms (P95)
- ✅ 测试覆盖率 > 85%
- ✅ 生产环境稳定运行

---

## 🔧 开发环境设置

### 1. 克隆项目

```bash
# Nautilus (已有)
cd C:/Users/chunx/Projects/nautilus-core/phase3

# Automaton
cd C:/Users/chunx/Projects
git clone https://github.com/Conway-Research/automaton.git
cd automaton
npm install
npm run build
```
### 2. 安装依赖

```bash
# Nautilus后端
cd C:/Users/chunx/Projects/nautilus-core/phase3/backend
pip install -r requirements.txt

# 新增依赖
pip install viem httpx croniter
```

### 3. 配置环境变量

```bash
# .env
EVOMAP_HUB_URL=https://evomap.ai
CONWAY_API_URL=https://api.conway.tech
CONWAY_API_KEY=your_api_key
ETHEREUM_RPC_URL=https://mainnet.base.org
USDC_CONTRACT_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
```

### 4. 创建测试钱包

```python
from viem import PrivateKeyAccount
import json

# 生成新钱包
wallet = PrivateKeyAccount.generate()

# 保存到文件
wallet_data = {
    "address": wallet.address,
    "private_key": wallet.key.hex()
}

with open("test_wallet.json", "w") as f:
    json.dump(wallet_data, f)

print(f"Wallet address: {wallet.address}")
print("⚠️ 请妥善保管私钥！")
```

### 5. 获取测试USDC

访问 Base Sepolia测试网水龙头:
- https://www.alchemy.com/faucets/base-sepolia
- 获取测试ETH
- 使用Uniswap获取测试USDC

---

## 🧪 测试命令

### 单元测试

```bash
# 测试A2A客户端
pytest tests/test_a2a_client.py -v

# 测试财务系统
pytest tests/test_financial_system.py -v

# 测试策略引擎
pytest tests/test_policy_engine.py -v

# 测试心跳系统
pytest tests/test_heartbeat.py -v

# 测试Super Agent
pytest tests/test_super_agent.py -v

# 所有测试
pytest tests/ -v --cov=. --cov-report=html
```

### 集成测试

```bash
# EvoMap集成测试
pytest tests/integration/test_evomap_integration.py -v

# Automaton集成测试
pytest tests/integration/test_automaton_integration.py -v

# 完整集成测试
pytest tests/integration/ -v
```

### 性能测试

```bash
# 任务执行性能
pytest tests/performance/test_performance.py -v

# EvoMap查询性能
pytest tests/performance/test_evomap_performance.py -v

# 生成性能报告
pytest tests/performance/ -v --benchmark-only
```

---

## 📊 监控命令

### Prometheus指标

```bash
# 查看所有指标
curl http://localhost:9090/metrics

# 查看EvoMap指标
curl http://localhost:9090/metrics | grep evomap

# 查看Automaton指标
curl http://localhost:9090/metrics | grep automaton

# 查看Super Agent指标
curl http://localhost:9090/metrics | grep super_agent
```

### 日志查看

```bash
# 查看Super Agent日志
tail -f /var/log/super_agent.log

# 查看心跳日志
tail -f /var/log/super_agent.log | grep heartbeat

# 查看策略决策日志
tail -f /var/log/super_agent.log | grep policy

# 查看财务日志
tail -f /var/log/super_agent.log | grep financial
```

---

## 🐛 故障排查

### 常见问题

#### 1. EvoMap连接失败

**症状**: `ConnectionError: Failed to connect to EvoMap`

**解决方案**:
```bash
# 检查网络连接
curl https://evomap.ai/health

# 检查API密钥
echo $EVOMAP_API_KEY

# 检查防火墙
sudo ufw status
```

#### 2. USDC余额为0

**症状**: `InsufficientFundsError: USDC balance is 0`

**解决方案**:
```bash
# 检查钱包地址
python -c "from viem import PrivateKeyAccount; import json; wallet = json.load(open('wallet.json')); print(wallet['address'])"

# 访问水龙头获取测试USDC
# https://www.alchemy.com/faucets/base-sepolia
```

#### 3. 策略引擎拒绝操作

**症状**: `PolicyDeniedError: Operation denied by policy engine`

**解决方案**:
```python
# 检查策略日志
from automaton_integration.policy_engine import AutomatonPolicyEngine

engine = AutomatonPolicyEngine()
# 查看最近的拒绝记录
# SELECT * FROM automaton_policy_decisions WHERE decision='deny' ORDER BY created_at DESC LIMIT 10;
```

#### 4. 心跳任务未执行

**症状**: 心跳任务长时间未执行

**解决方案**:
```python
# 检查心跳守护进程状态
from automaton_integration.heartbeat import HeartbeatDaemon

# 查看心跳日志
# SELECT * FROM automaton_heartbeat_logs ORDER BY created_at DESC LIMIT 20;

# 手动触发心跳任务
# daemon.heartbeat.forceRun("check_credits")
```

---

## 📞 获取帮助

### 文档资源

- **Nautilus文档**: `C:/Users/chunx/Projects/nautilus-core/phase3/README.md`
- **Automaton文档**: `C:/Users/chunx/Projects/automaton-analysis/DOCUMENTATION.md`
- **EvoMap Wiki**: https://evomap.ai/wiki

### 社区支持

- **Nautilus GitHub**: https://github.com/chunxiaoxx/nautilus-core
- **Automaton GitHub**: https://github.com/Conway-Research/automaton
- **EvoMap平台**: https://evomap.ai

### 联系方式

- **技术问题**: 查看相关文档或GitHub Issues
- **紧急问题**: 查看故障排查章节

---

## 🎯 关键指标

### 性能指标

| 指标 | 目标值 | 当前值 | 状态 |
|------|--------|------|------|
| API响应时间 (P95) | < 200ms | - | 待测试 |
| EvoMap查询延迟 (P95) | < 500ms | - | 待测试 |
| 任务执行成功率 | > 95% | - | 待测试 |
| 系统可用性 | > 99.5% | - | 待测试 |

### 质量指标

| 指标 | 目标值 | 当前值 | 状态 |
|------|--------|------|------|
| 测试覆盖率 | > 85% | - | 待测试 |
| 代码审查通过率 | 100% | - | 待审查 |
| 安全审计 | 通过 | - | 待审计 |
| 文档完整性 | 100% | 100% | ✅ 完成 |

### 业务指标

| 指标 | 目标值 | 说明 |
|------|--------|----|
| 任务成功率提升 | +27% | 通过EvoMap最佳实践 |
| 执行效率提升 | +60% | 避免重复计算 |
| 能源消耗降低 | -90% | 能力继承 |
| 系统稳定性提升 | +12% | Automaton策略引擎 |

---

## 🚀 快速开始

### 5分钟快速体验

```python
# quick_start.py

import asyncio
from super_agent.agent import SuperAgent

async def main():
    # 1. 创建Super Agent
    agent = SuperAgent(
        agent_id="demo_agent",
      wallet_address="0x...",  # 你的测试钱包地址
        evomap_hub_url="https://evomap.ai"
    )

    # 2. 启动Agent
    print("🚀 Starting Super Agent...")
    await agent.start()

    # 3. 执行简单任务
    print("📋 Executing task...")
    task = {
        "id": "demo_task",
    "type": "test",
        "description": "Test task",
        "tool": "echo",
        "args": {"message": "Hello Super Agent!"}
    }

    result = await agent.execute_task(task)
    print(f"✅ Task result: {result}")

    # 4. 检查状态
    print(f"💰 Survival tier: {agent.survival_tier}")
    print(f"💵 Balance: ${agent.financial_system.credit_balance/100:.2f}")

    # 5. 停止Agent
    print("🛑 Stopping Super Agent...")
    await agent.stop()
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
```

运行:
```bash
python quick_start.py
```

---

## 📝 更新日志

### Version 1.0 (2026-03-04)

**新增**:
- ✅ 完整的Super Agent集成方案
- ✅ 三层架构设计
- ✅ 5个阶段的实施路线图
- ✅ ~2,300行Python代码示例
- ✅ 完整的测试策略
- ✅ 监控和可观测性方案

**文档**:
- ✅ SUPER_AGENT_FINAL_SUMMARY.md
- ✅ SUPER_AGENT_INTEGRATION_PLAN.md (Part 1-3)
- ✅ SUPER_AGENT_QUICK_REFERENCE.md (本文档)
- ✅ AUTOMATON_INTEGRATION_PLAN.md

---

**文档版本**: 1.0
**最后更新**: 2026-03-04
**维护者**: Claude Sonnet 4.6
**下次更新**: Phase 1完成后

🎉 **准备好开始构建Super Agent了吗？从Phase 1开始吧！**
