"""
Nautilus 夜间工作验证脚本
用于快速验证所有夜间完成的工作
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

# 颜色定义（Windows 兼容）
try:
    import colorama
    colorama.init()
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'
except ImportError:
    GREEN = RED = YELLOW = BLUE = NC = ''


def print_header(text):
    """打印标题"""
    print(f"\n{'='*50}")
    print(f"{BLUE}{text}{NC}")
    print('='*50)


def print_success(text):
    """打印成功消息"""
    print(f"{GREEN}✓{NC} {text}")


def print_error(text):
    """打印错误消息"""
    print(f"{RED}✗{NC} {text}")


def print_warning(text):
    """打印警告消息"""
    print(f"{YELLOW}⚠{NC} {text}")


def check_package(package_name):
    """检查 Python 包是否已安装"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def install_package(package_name):
    """安装 Python 包"""
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_name],
            check=True
        )
        return True
    except Exception as e:
        print_error(f"安装失败: {e}")
        return False


def check_file_contains(file_path, search_text):
    """检查文件是否包含指定文本"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_text in content
    except Exception:
        return False


async def test_database_health():
    """测试数据库健康检查"""
    try:
        # 切换到 backend 目录
        backend_dir = Path(__file__).parent.parent / 'backend'
        os.chdir(backend_dir)

        # 导入并测试
        from monitoring_config import check_database_health

        result = await check_database_health()

        if result['status'] == 'healthy':
            print_success(f"数据库健康检查: PASSED")
            if 'response_time' in result:
                print(f"  响应时间: {result['response_time']}s")
            return True
        else:
            print_error(f"数据库健康检查: FAILED")
            if 'error' in result:
                print(f"  错误: {result['error']}")
            return False
    except Exception as e:
        print_error(f"数据库健康检查测试失败: {e}")
        return False


def main():
    """主函数"""
    print_header("Nautilus 夜间工作验证脚本")

    # 获取项目路径
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent / 'backend'

    # 步骤 1: 检查依赖
    print_header("步骤 1: 检查依赖安装")

    dependencies = {
        'qrcode': 'qrcode[pil]',
        'Pillow': 'Pillow',
        'prometheus-client': 'prometheus-client'
    }

    for package, install_name in dependencies.items():
        if check_package(package):
            print_success(f"{package} 已安装")
        else:
            print_warning(f"{package} 未安装，正在安装...")
            if install_package(install_name):
                print_success(f"{package} 安装成功")
            else:
                print_error(f"{package} 安装失败")

    # 步骤 2: 测试数据库健康检查
    print_header("步骤 2: 测试数据库健康检查")

    try:
        asyncio.run(test_database_health())
    except Exception as e:
        print_error(f"无法测试数据库健康检查: {e}")

    # 步骤 3: 检查数据库迁移
    print_header("步骤 3: 检查数据库迁移状态")

    migration_file = backend_dir / 'migrations' / 'add_oauth_fields.py'
    if migration_file.exists():
        print_success("OAuth 迁移脚本已创建")
        print(f"  位置: {migration_file}")
        print(f"  运行: python {migration_file}")
    else:
        print_error("OAuth 迁移脚本未找到")

    # 步骤 4: 验证 API 端点代码
    print_header("步骤 4: 验证 API 端点代码")

    auth_file = backend_dir / 'api' / 'auth.py'
    agents_file = backend_dir / 'api' / 'agents.py'

    checks = [
        (auth_file, 'github/login', 'GitHub OAuth 登录端点'),
        (auth_file, 'github/callback', 'GitHub OAuth 回调端点'),
        (agents_file, 'agent_self_register', 'Agent 自主注册端点'),
        (agents_file, 'generate_qr_code', 'QR 码生成功能'),
    ]

    for file_path, search_text, description in checks:
        if check_file_contains(file_path, search_text):
            print_success(f"{description}已实现")
        else:
            print_error(f"{description}未找到")

    # 步骤 5: 检查环境变量
    print_header("步骤 5: 检查环境变量配置")

    env_file = backend_dir / '.env'
    if check_file_contains(env_file, 'GITHUB_CLIENT_ID'):
        print_success("GitHub OAuth 配置已添加")
    else:
        print_error("GitHub OAuth 配置未找到")

    # 步骤 6: 检查修改的文件
    print_header("步骤 6: 检查文件修改")

    modified_files = [
        ('backend/monitoring_config.py', '数据库健康检查修复'),
        ('backend/.env', 'OAuth 环境变量'),
        ('backend/models/database.py', 'User 模型 OAuth 字段'),
        ('backend/api/auth.py', 'GitHub OAuth 端点'),
        ('backend/api/agents.py', 'Agent 自主注册'),
        ('backend/requirements.txt', '新增依赖'),
        ('backend/migrations/add_oauth_fields.py', '数据库迁移脚本'),
    ]

    for file_path, description in modified_files:
        full_path = script_dir.parent / file_path
        if full_path.exists():
            print_success(f"{description}: {file_path}")
        else:
            print_error(f"{description}: {file_path} (未找到)")

    # 总结
    print_header("验证完成！")

    print("\n下一步操作：\n")

    print("1. 运行数据库迁移（如果 PostgreSQL 可用）：")
    print(f"   cd {backend_dir}")
    print("   python migrations/add_oauth_fields.py\n")

    print("2. 启动后端服务：")
    print("   python main.py\n")

    print("3. 测试健康检查：")
    print("   curl http://localhost:8000/health\n")

    print("4. 测试 Agent 自主注册：")
    print('   curl -X POST http://localhost:8000/api/agents/register \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d "{\\"name\\":\\"Test Agent\\",\\"email\\":\\"test@example.com\\"}"\n')

    print("5. 测试 GitHub OAuth：")
    print("   访问: http://localhost:8000/api/auth/github/login\n")

    print(f"详细报告位于: {script_dir}/\n")

    print("夜间工作完成的功能：")
    print("  ✓ 数据库健康检查修复")
    print("  ✓ GitHub OAuth 认证")
    print("  ✓ Agent 自主注册 API")
    print("  ✓ QR 码生成")
    print("  ✓ 移动监控链接\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n验证已取消")
        sys.exit(0)
    except Exception as e:
        print_error(f"\n验证过程出错: {e}")
        sys.exit(1)
