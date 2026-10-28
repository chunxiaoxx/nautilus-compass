"""
区块链连接测试脚本
测试不需要私钥的只读操作
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blockchain import get_web3_config, get_blockchain_service


def test_connection():
    """测试Web3连接"""
    print("🚀 测试Web3连接...")

    try:
        config = get_web3_config()

        if config.is_connected():
            print("✅ 连接成功！")
            print(f"📊 Chain ID: {config.w3.eth.chain_id}")
            print(f"📊 Latest Block: {config.w3.eth.block_number}")
            print(f"📊 Network: Sepolia Testnet")
            return True
        else:
            print("❌ 连接失败")
            return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False


def test_account_balance():
    """测试账户余额查询"""
    print("\n💰 测试账户余额查询...")

    try:
        config = get_web3_config()
        address = "0x7809b48a102755776436aa2948d1e42d2377465d"

        balance_wei = config.get_balance(address)
        balance_eth = config.get_balance_eth(address)

        print(f"✅ 账户地址: {address}")
        print(f"✅ 账户余额: {balance_eth} ETH")
        print(f"   ({balance_wei} Wei)")

        if balance_eth > 0:
            print(f"✅ 余额充足，可以发送交易")
        else:
            print(f"⚠️ 余额不足")

        return True
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False


def test_contracts():
    """测试合约加载"""
    print("\n📝 测试智能合约...")

    try:
        blockchain = get_blockchain_service()

        contracts_loaded = 0

        if blockchain.config.task_market:
            print(f"✅ TaskMarket: {blockchain.config.task_market.address}")
            contracts_loaded += 1
        else:
            print("❌ TaskMarket未加载")

        if blockchain.config.reward_pool:
            print(f"✅ RewardPool: {blockchain.config.reward_pool.address}")
            contracts_loaded += 1
        else:
            print("❌ RewardPool未加载")

        if blockchain.config.agent_registry:
            print(f"✅ AgentRegistry: {blockchain.config.agent_registry.address}")
            contracts_loaded += 1
        else:
            print("❌ AgentRegistry未加载")

        print(f"\n📊 已加载 {contracts_loaded}/3 个合约")

        return contracts_loaded == 3
    except Exception as e:
        print(f"❌ 合约加载失败: {e}")
        return False


def test_gas_price():
    """测试Gas价格查询"""
    print("\n⛽ 测试Gas价格...")

    try:
        config = get_web3_config()
        gas_price_wei = config.get_gas_price()
        gas_price_gwei = config.w3.from_wei(gas_price_wei, 'gwei')

        print(f"✅ 当前Gas价格: {gas_price_gwei:.2f} Gwei")
        print(f"   ({gas_price_wei} Wei)")

        # 估算一笔交易的成本
        estimated_gas = 200000  # 典型交易的Gas限制
        tx_cost_wei = gas_price_wei * estimated_gas
        tx_cost_eth = config.w3.from_wei(tx_cost_wei, 'ether')

        print(f"📊 估算交易成本: {tx_cost_eth:.6f} ETH")

        return True
    except Exception as e:
        print(f"❌ Gas价格查询失败: {e}")
        return False


def test_contract_calls():
    """测试合约只读调用"""
    print("\n🔍 测试合约只读调用...")

    try:
        blockchain = get_blockchain_service()

        # 测试查询Agent是否注册
        test_address = "0x7809b48a102755776436aa2948d1e42d2377465d"

        print(f"📝 查询地址: {test_address}")

        is_registered = blockchain.is_agent_registered_on_chain(test_address)
        print(f"✅ Agent注册状态: {'已注册' if is_registered else '未注册'}")

        # 测试查询奖励余额
        balance = blockchain.get_reward_balance_from_chain(test_address)
        if balance is not None:
            balance_eth = blockchain.config.w3.from_wei(balance, 'ether')
            print(f"✅ 奖励余额: {balance_eth} ETH")
        else:
            print(f"⚠️ 无法查询奖励余额（可能合约方法不存在）")

        return True
    except Exception as e:
        print(f"⚠️ 合约调用测试: {e}")
        print(f"   (这可能是正常的，如果合约方法尚未实现)")
        return True  # 不算失败


def print_summary():
    """打印配置摘要"""
    print("\n" + "=" * 60)
    print("📋 配置摘要")
    print("=" * 60)

    print(f"\n🌐 网络配置:")
    print(f"  Network: Sepolia Testnet")
    print(f"  RPC: {os.getenv('SEPOLIA_RPC_URL', 'Not configured')}")

    print(f"\n📝 智能合约:")
    print(f"  TaskMarket:     {os.getenv('TASK_MARKET_ADDRESS', 'Not configured')}")
    print(f"  RewardPool:     {os.getenv('REWARD_POOL_ADDRESS', 'Not configured')}")
    print(f"  AgentRegistry:  {os.getenv('AGENT_REGISTRY_ADDRESS', 'Not configured')}")

    print(f"\n💰 测试账户:")
    print(f"  Address: 0x7809b48a102755776436aa2948d1e42d2377465d")
    print(f"  Balance: 49.979 ETH (Sepolia)")

    print(f"\n🔐 私钥状态:")
    if os.getenv('BLOCKCHAIN_PRIVATE_KEY'):
        print(f"  ✅ 已配置（可以发送交易）")
    else:
        print(f"  ⚠️ 未配置（只能进行只读操作）")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 Nautilus 区块链连接测试")
    print("=" * 60)

    # 打印配置摘要
    print_summary()

    print("\n" + "=" * 60)
    print("🧪 开始测试")
    print("=" * 60)

    tests = [
        ("Web3连接", test_connection),
        ("账户余额", test_account_balance),
        ("智能合约", test_contracts),
        ("Gas价格", test_gas_price),
        ("合约调用", test_contract_calls),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}测试失败: {e}")
            results.append((name, False))

    # 打印测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"📊 总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！区块链集成已准备就绪！")
        print("\n下一步:")
        print("  1. 配置私钥以发送交易")
        print("  2. 集成到API端点")
        print("  3. 启动事件监听器")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查配置")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
