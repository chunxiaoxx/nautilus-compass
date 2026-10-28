#!/usr/bin/env python3
"""
密钥管理测试脚本
测试各种密钥管理功能
"""
import os
import sys
import tempfile
import secrets
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from blockchain.key_manager import (
    KeyManager,
    KeySource,
    KeyRotationPolicy,
    KeyEncryption,
    get_key_manager
)


def test_environment_source():
    """测试环境变量源"""
    print("\n" + "="*60)
    print("测试 1: 环境变量源")
    print("="*60)

    try:
        # 设置测试密钥
        test_key = "0x" + secrets.token_hex(32)
        os.environ['BLOCKCHAIN_PRIVATE_KEY'] = test_key

        # 创建管理器
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)

        # 验证
        loaded_key = manager.get_private_key()
        assert loaded_key == test_key, "密钥不匹配"
        assert manager.validate_key(), "密钥验证失败"

        address = manager.get_public_address()
        assert address is not None, "无法获取地址"

        print(f"✅ 密钥加载: {manager.mask_key(loaded_key)}")
        print(f"✅ 密钥验证: 通过")
        print(f"✅ 地址: {address}")
        print("✅ 测试通过")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_encrypted_file():
    """测试加密文件存储"""
    print("\n" + "="*60)
    print("测试 2: 加密文件存储")
    print("="*60)

    try:
        # 生成测试数据
        test_key = "0x" + secrets.token_hex(32)
        test_password = "test_password_" + secrets.token_hex(8)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            # 保存加密密钥
            print(f"保存到: {temp_file}")
            manager = KeyManager(
                key_source=KeySource.ENCRYPTED_FILE,
                key_file_path=temp_file,
                encryption_password=test_password
            )
            manager.save_encrypted_key(test_key, temp_file)
            print("✅ 密钥已加密保存")

            # 加载加密密钥
            load_manager = KeyManager(
                key_source=KeySource.ENCRYPTED_FILE,
                key_file_path=temp_file,
                encryption_password=test_password
            )

            loaded_key = load_manager.get_private_key()
            assert loaded_key == test_key, "密钥不匹配"
            print(f"✅ 密钥加载: {load_manager.mask_key(loaded_key)}")

            # 验证元数据
            metadata = load_manager.get_metadata()
            assert metadata is not None, "元数据为空"
            assert metadata.source == KeySource.ENCRYPTED_FILE, "源类型不匹配"
            print(f"✅ 元数据: Key ID={metadata.key_id}, Created={metadata.created_at}")

            print("✅ 测试通过")
            return True

        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"✅ 清理临时文件: {temp_file}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_key_validation():
    """测试密钥验证"""
    print("\n" + "="*60)
    print("测试 3: 密钥验证")
    print("="*60)

    try:
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)

        # 测试有效密钥
        valid_keys = [
            "0x" + secrets.token_hex(32),
            secrets.token_hex(32),  # 无0x前缀
        ]

        for key in valid_keys:
            manager._private_key = key
            assert manager.validate_key(), f"有效密钥验证失败: {manager.mask_key(key)}"
            print(f"✅ 有效密钥: {manager.mask_key(key)}")

        # 测试无效密钥
        invalid_keys = [
            "0x123",  # 太短
            "0x" + "g" * 64,  # 非十六进制
            "invalid",  # 完全无效
        ]

        for key in invalid_keys:
            manager._private_key = key
            assert not manager.validate_key(), f"无效密钥未被检测: {key}"
            print(f"✅ 无效密钥检测: {manager.mask_key(key)}")

        print("✅ 测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_key_rotation():
    """测试密钥轮换"""
    print("\n" + "="*60)
    print("测试 4: 密钥轮换")
    print("="*60)

    try:
        # 生成测试数据
        old_key = "0x" + secrets.token_hex(32)
        new_key = "0x" + secrets.token_hex(32)
        test_password = "test_password_" + secrets.token_hex(8)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            # 保存初始密钥
            manager = KeyManager(
                key_source=KeySource.ENCRYPTED_FILE,
                key_file_path=temp_file,
                encryption_password=test_password
            )
            manager.save_encrypted_key(old_key, temp_file)

            # 重新加载
            manager = KeyManager(
                key_source=KeySource.ENCRYPTED_FILE,
                key_file_path=temp_file,
                encryption_password=test_password
            )

            old_address = manager.get_public_address()
            old_rotation_count = manager.get_metadata().rotation_count
            print(f"旧地址: {old_address}")
            print(f"轮换次数: {old_rotation_count}")

            # 轮换密钥
            manager.rotate_key(new_key)
            print("✅ 密钥已轮换")

            # 验证新密钥
            loaded_key = manager.get_private_key()
            assert loaded_key == new_key, "新密钥不匹配"

            new_address = manager.get_public_address()
            new_rotation_count = manager.get_metadata().rotation_count
            print(f"新地址: {new_address}")
            print(f"轮换次数: {new_rotation_count}")

            assert new_address != old_address, "地址未改变"
            assert new_rotation_count == old_rotation_count + 1, "轮换计数未增加"

            # 验证备份文件
            backup_files = [f for f in os.listdir(os.path.dirname(temp_file))
                          if f.startswith(os.path.basename(temp_file) + '.backup')]
            assert len(backup_files) > 0, "未创建备份文件"
            print(f"✅ 备份文件: {len(backup_files)} 个")

            print("✅ 测试通过")
            return True

        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            # 清理备份文件
            for backup in backup_files:
                backup_path = os.path.join(os.path.dirname(temp_file), backup)
                if os.path.exists(backup_path):
                    os.remove(backup_path)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_encryption_decryption():
    """测试加密解密"""
    print("\n" + "="*60)
    print("测试 5: 加密解密")
    print("="*60)

    try:
        test_key = "0x" + secrets.token_hex(32)
        test_password = "test_password_" + secrets.token_hex(8)

        # 加密
        encrypted_data = KeyEncryption.encrypt_key(test_key, test_password)
        assert 'encrypted_key' in encrypted_data, "缺少加密密钥"
        assert 'salt' in encrypted_data, "缺少盐值"
        assert 'algorithm' in encrypted_data, "缺少算法"
        print(f"✅ 加密成功: 算法={encrypted_data['algorithm']}")

        # 解密
        decrypted_key = KeyEncryption.decrypt_key(encrypted_data, test_password)
        assert decrypted_key == test_key, "解密后密钥不匹配"
        print(f"✅ 解密成功")

        # 测试错误密码
        try:
            wrong_password = "wrong_password"
            KeyEncryption.decrypt_key(encrypted_data, wrong_password)
            assert False, "错误密码应该失败"
        except Exception:
            print(f"✅ 错误密码检测成功")

        print("✅ 测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rotation_policy():
    """测试轮换策略"""
    print("\n" + "="*60)
    print("测试 6: 轮换策略")
    print("="*60)

    try:
        # 创建轮换策略
        policy = KeyRotationPolicy(
            enabled=True,
            rotation_days=90,
            warning_days=7
        )

        assert policy.enabled == True, "策略未启用"
        assert policy.rotation_days == 90, "轮换天数不匹配"
        assert policy.warning_days == 7, "警告天数不匹配"
        print(f"✅ 策略创建: rotation_days={policy.rotation_days}, warning_days={policy.warning_days}")

        # 测试策略应用
        test_key = "0x" + secrets.token_hex(32)
        os.environ['BLOCKCHAIN_PRIVATE_KEY'] = test_key

        manager = KeyManager(
            key_source=KeySource.ENVIRONMENT,
            rotation_policy=policy
        )

        assert manager.rotation_policy.enabled == True, "管理器策略未启用"
        print(f"✅ 策略应用成功")

        print("✅ 测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_key_masking():
    """测试密钥遮蔽"""
    print("\n" + "="*60)
    print("测试 7: 密钥遮蔽")
    print("="*60)

    try:
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)

        # 测试不同长度的密钥
        test_cases = [
            ("0x" + "a" * 64, "0xaaaa...aaaa"),
            ("short", "***"),
            ("", "None"),
            (None, "None"),
        ]

        for key, expected_pattern in test_cases:
            masked = manager.mask_key(key)
            if expected_pattern == "***":
                assert masked == "***", f"短密钥遮蔽失败: {masked}"
            elif expected_pattern == "None":
                assert masked == "None", f"空密钥遮蔽失败: {masked}"
            else:
                assert masked.startswith(key[:6]) and masked.endswith(key[-4:]), f"密钥遮蔽失败: {masked}"
            print(f"✅ 遮蔽: {key[:20] if key else 'None'}... -> {masked}")

        print("✅ 测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_singleton_pattern():
    """测试单例模式"""
    print("\n" + "="*60)
    print("测试 8: 单例模式")
    print("="*60)

    try:
        # 设置测试环境
        test_key = "0x" + secrets.token_hex(32)
        os.environ['BLOCKCHAIN_PRIVATE_KEY'] = test_key
        os.environ['KEY_SOURCE'] = 'environment'

        # 获取两次实例
        manager1 = get_key_manager()
        manager2 = get_key_manager()

        # 验证是同一个实例
        assert manager1 is manager2, "不是同一个实例"
        print(f"✅ 单例验证: manager1 is manager2")

        # 验证密钥相同
        key1 = manager1.get_private_key()
        key2 = manager2.get_private_key()
        assert key1 == key2, "密钥不匹配"
        print(f"✅ 密钥一致: {manager1.mask_key(key1)}")

        print("✅ 测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🔐 密钥管理器测试套件")
    print("="*60)

    tests = [
        test_environment_source,
        test_encrypted_file,
        test_key_validation,
        test_key_rotation,
        test_encryption_decryption,
        test_rotation_policy,
        test_key_masking,
        test_singleton_pattern,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ 测试异常: {test.__name__}")
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))

    # 打印总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 通过")
    print("="*60)

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
