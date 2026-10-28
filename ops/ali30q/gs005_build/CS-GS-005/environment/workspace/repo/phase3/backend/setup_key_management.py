#!/usr/bin/env python3
"""
密钥管理配置脚本
自动生成密钥文件和配置环境变量
"""
import sys
import os
from pathlib import Path
import secrets
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from blockchain.key_manager import KeyManager, KeySource


def setup_key_management():
    """配置密钥管理"""
    print("🔐 密钥管理配置工具")
    print("=" * 60)

    # 1. 创建keys目录
    keys_dir = Path(__file__).parent / "keys"
    keys_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {keys_dir}")

    # 2. 生成测试密钥
    print("\n📝 生成测试密钥...")
    private_key = "0x" + secrets.token_hex(32)
    password = "SecureTestPassword2024!@#"

    # 3. 保存加密密钥
    key_file_path = keys_dir / "blockchain_key.json"

    manager = KeyManager(
        key_source=KeySource.ENCRYPTED_FILE,
        key_file_path=str(key_file_path),
        encryption_password=password
    )

    manager.save_encrypted_key(private_key, str(key_file_path))
    print(f"✅ 密钥文件已保存: {key_file_path}")

    # 获取地址
    manager._private_key = private_key
    address = manager.get_public_address()
    print(f"✅ 生成地址: {address}")
    print(f"✅ 密钥（遮蔽）: {manager.mask_key(private_key)}")

    # 4. 读取现有.env文件
    env_file = Path(__file__).parent / ".env"
    env_lines = []

    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()

    # 5. 更新或添加密钥管理配置
    key_configs = {
        'KEY_SOURCE': 'encrypted_file',
        'KEY_FILE_PATH': './keys/blockchain_key.json',
        'KEY_ENCRYPTION_PASSWORD': password,
        'KEY_ROTATION_ENABLED': 'true',
        'KEY_ROTATION_DAYS': '90'
    }

    # 移除旧的密钥配置
    new_lines = []
    for line in env_lines:
        if not any(line.startswith(f"{key}=") for key in key_configs.keys()):
            new_lines.append(line)

    # 添加新配置
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines.append('\n')

    new_lines.append('\n# 密钥管理配置\n')
    for key, value in key_configs.items():
        new_lines.append(f'{key}={value}\n')

    # 6. 写入.env文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"\n✅ 环境变量已配置: {env_file}")

    # 7. 验证配置
    print("\n🔍 验证配置...")
    verify_manager = KeyManager(
        key_source=KeySource.ENCRYPTED_FILE,
        key_file_path=str(key_file_path),
        encryption_password=password
    )

    loaded_key = verify_manager.get_private_key()
    if loaded_key == private_key:
        print("✅ 密钥加载验证成功")
    else:
        print("❌ 密钥加载验证失败")
        return False

    # 8. 生成配置摘要
    print("\n" + "=" * 60)
    print("📋 配置摘要")
    print("=" * 60)
    print(f"密钥文件: {key_file_path}")
    print(f"密钥源: encrypted_file")
    print(f"密钥轮换: 启用 (90天)")
    print(f"区块链地址: {address}")
    print(f"加密密码: {password[:8]}... (已保存到.env)")
    print("=" * 60)

    # 9. 保存配置信息到文件
    config_info = {
        "key_file": str(key_file_path),
        "key_source": "encrypted_file",
        "address": address,
        "rotation_enabled": True,
        "rotation_days": 90,
        "created_at": manager.get_metadata().created_at.isoformat() if manager.get_metadata() else None
    }

    info_file = Path(__file__).parent / "keys" / "config_info.json"
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(config_info, f, indent=2)

    print(f"\n✅ 配置信息已保存: {info_file}")
    print("\n✅ 密钥管理配置完成！")

    return True


if __name__ == "__main__":
    try:
        success = setup_key_management()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 配置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
