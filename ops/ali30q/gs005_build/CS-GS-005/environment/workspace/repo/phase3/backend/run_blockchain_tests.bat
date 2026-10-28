@echo off
REM 区块链集成测试运行脚本 (Windows版本)

echo ==========================================
echo 区块链集成测试套件
echo ==========================================
echo.

REM 检查依赖
echo 检查依赖...
python -c "import web3" 2>nul
if errorlevel 1 (
    echo ❌ web3未安装，正在安装...
    pip install web3>=6.0.0 eth-account>=0.9.0
    if errorlevel 1 (
        echo ❌ 安装失败，请手动安装: pip install web3 eth-account
        exit /b 1
    )
)

python -c "import pytest" 2>nul
if errorlevel 1 (
    echo ❌ pytest未安装，正在安装...
    pip install pytest pytest-asyncio
    if errorlevel 1 (
        echo ❌ 安装失败，请手动安装: pip install pytest pytest-asyncio
        exit /b 1
    )
)

echo ✅ 依赖检查完成
echo.

REM 显示菜单
echo 请选择测试模式：
echo 1) Mock测试（快速，不需要区块链连接）
echo 2) 测试网络测试（需要配置环境变量）
echo 3) 运行所有测试
echo 4) 运行特定测试类
echo 5) 查看测试列表
echo 6) 生成覆盖率报告
echo.

set /p choice="请输入选项 (1-6): "

if "%choice%"=="1" (
    echo.
    echo 运行Mock测试...
    pytest tests/test_blockchain_integration.py -v -k "not test_e2e" --tb=short
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 检查环境变量...
    if "%SEPOLIA_RPC_URL%"=="" if "%INFURA_PROJECT_ID%"=="" (
        echo ⚠️  警告: 未配置SEPOLIA_RPC_URL或INFURA_PROJECT_ID
        echo 请设置环境变量后再运行测试网络测试
        exit /b 1
    )
    echo 运行测试网络测试...
    pytest tests/test_blockchain_integration.py -v -k "test_e2e" --tb=short
    goto end
)

if "%choice%"=="3" (
    echo.
    echo 运行所有测试...
    pytest tests/test_blockchain_integration.py -v --tb=short
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 可用的测试类：
    echo 1) TestTaskMarketIntegration - TaskMarket合约测试
    echo 2) TestRewardPoolIntegration - RewardPool合约测试
    echo 3) TestAgentRegistryIntegration - AgentRegistry合约测试
    echo 4) TestGasFeeSharing - Gas费用测试
    echo 5) TestErrorHandlingAndRetry - 错误处理测试
    echo 6) TestTransactionFailureScenarios - 交易失败场景测试
    echo 7) TestWeb3Config - Web3配置测试
    echo 8) TestBlockchainEventListener - 事件监听器测试
    echo 9) TestEndToEndIntegration - 端到端测试
    echo 10) TestPerformanceAndStress - 性能测试
    echo.
    set /p test_class="请输入测试类编号 (1-10): "

    if "%test_class%"=="1" pytest tests/test_blockchain_integration.py::TestTaskMarketIntegration -v
    if "%test_class%"=="2" pytest tests/test_blockchain_integration.py::TestRewardPoolIntegration -v
    if "%test_class%"=="3" pytest tests/test_blockchain_integration.py::TestAgentRegistryIntegration -v
    if "%test_class%"=="4" pytest tests/test_blockchain_integration.py::TestGasFeeSharing -v
    if "%test_class%"=="5" pytest tests/test_blockchain_integration.py::TestErrorHandlingAndRetry -v
    if "%test_class%"=="6" pytest tests/test_blockchain_integration.py::TestTransactionFailureScenarios -v
    if "%test_class%"=="7" pytest tests/test_blockchain_integration.py::TestWeb3Config -v
    if "%test_class%"=="8" pytest tests/test_blockchain_integration.py::TestBlockchainEventListener -v
    if "%test_class%"=="9" pytest tests/test_blockchain_integration.py::TestEndToEndIntegration -v
    if "%test_class%"=="10" pytest tests/test_blockchain_integration.py::TestPerformanceAndStress -v
    goto end
)

if "%choice%"=="5" (
    echo.
    echo 测试列表：
    pytest tests/test_blockchain_integration.py --collect-only -q
    goto end
)

if "%choice%"=="6" (
    echo.
    echo 生成覆盖率报告...
    pytest tests/test_blockchain_integration.py --cov=blockchain --cov-report=html --cov-report=term -v
    echo.
    echo ✅ 覆盖率报告已生成到 htmlcov/index.html
    goto end
)

echo 无效选项
exit /b 1

:end
echo.
echo ==========================================
echo 测试完成
echo ==========================================
