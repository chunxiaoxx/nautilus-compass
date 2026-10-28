"""
密钥管理命令行工具
提供密钥加密、解密、验证等功能
"""
import sys
import argparse
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from blockchain.key_manager import KeyManager, KeySource, KeyRotationPolicy
import secrets


def cmd_encrypt(args):
    """加密私钥"""
    try:
        manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.output,
            encryption_password=args.password
        )

        manager.save_encrypted_key(args.key, args.output)
        print(f'✅ Key encrypted and saved to {args.output}')

        # 显示地址
        manager._private_key = args.key
        address = manager.get_public_address()
        if address:
            print(f'✅ Address: {address}')

    except Exception as e:
        print(f'❌ Encryption failed: {e}')
        sys.exit(1)


def cmd_decrypt(args):
    """解密私钥"""
    try:
        manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.input,
            encryption_password=args.password
        )

        key = manager.get_private_key()
        if key:
            if args.show_full:
                print(f'✅ Decrypted key: {key}')
            else:
                print(f'✅ Decrypted key: {manager.mask_key(key)}')

            address = manager.get_public_address()
            if address:
                print(f'✅ Address: {address}')
        else:
            print('❌ Failed to decrypt key')
            sys.exit(1)

    except Exception as e:
        print(f'❌ Decryption failed: {e}')
        sys.exit(1)


def cmd_validate(args):
    """验证私钥"""
    try:
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)
        manager._private_key = args.key

        if manager.validate_key():
            print('✅ Key is valid')
            address = manager.get_public_address()
            if address:
                print(f'✅ Address: {address}')
        else:
            print('❌ Key is invalid')
            print('Key should be 64 hex characters with optional 0x prefix')
            sys.exit(1)

    except Exception as e:
        print(f'❌ Validation failed: {e}')
        sys.exit(1)


def cmd_generate(args):
    """生成新私钥"""
    try:
        # 生成随机私钥
        private_key = "0x" + secrets.token_hex(32)

        # 验证
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)
        manager._private_key = private_key

        if not manager.validate_key():
            print('❌ Generated key is invalid')
            sys.exit(1)

        # 获取地址
        address = manager.get_public_address()

        print('✅ New private key generated')
        if args.show_full:
            print(f'Private Key: {private_key}')
        else:
            print(f'Private Key: {manager.mask_key(private_key)}')
        print(f'Address: {address}')

        # 如果指定了输出文件，保存加密密钥
        if args.output and args.password:
            manager_file = KeyManager(
                key_source=KeySource.ENCRYPTED_FILE,
                key_file_path=args.output,
                encryption_password=args.password
            )
            manager_file.save_encrypted_key(private_key, args.output)
            print(f'✅ Encrypted key saved to {args.output}')

    except Exception as e:
        print(f'❌ Generation failed: {e}')
        sys.exit(1)


def cmd_rotate(args):
    """轮换密钥"""
    try:
        # 加载当前密钥
        manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.input,
            encryption_password=args.password
        )

        old_key = manager.get_private_key()
        if not old_key:
            print('❌ Failed to load current key')
            sys.exit(1)

        old_address = manager.get_public_address()
        print(f'Current address: {old_address}')

        # 生成新密钥
        if args.new_key:
            new_key = args.new_key
        else:
            new_key = "0x" + secrets.token_hex(32)
            print('✅ New key generated')

        # 轮换
        manager.rotate_key(new_key)

        new_address = manager.get_public_address()
        print(f'✅ Key rotated successfully')
        print(f'New address: {new_address}')

        # 显示元数据
        metadata = manager.get_metadata()
        if metadata:
            print(f'Rotation count: {metadata.rotation_count}')
            print(f'Last rotated: {metadata.last_rotated}')

    except Exception as e:
        print(f'❌ Rotation failed: {e}')
        sys.exit(1)


def cmd_info(args):
    """显示密钥信息"""
    try:
        # 根据源类型加载密钥
        if args.source == 'environment':
            manager = KeyManager(key_source=KeySource.ENVIRONMENT)
        elif args.source == 'encrypted_file':
            if not args.input or not args.password:
                print('❌ --input and --password required for encrypted_file source')
                sys.exit(1)
            manager = KeyManager(
                key_source=KeySource.ENCRYPTED_FILE,
                key_file_path=args.input,
                encryption_password=args.password
            )
        else:
            print(f'❌ Unsupported source: {args.source}')
            sys.exit(1)

        key = manager.get_private_key()
        if not key:
            print('❌ No key loaded')
            sys.exit(1)

        print('📊 Key Information:')
        print(f'  Source: {manager.key_source.value}')
        print(f'  Key: {manager.mask_key(key)}')
        print(f'  Valid: {manager.validate_key()}')

        address = manager.get_public_address()
        if address:
            print(f'  Address: {address}')

        metadata = manager.get_metadata()
        if metadata:
            print(f'  Key ID: {metadata.key_id}')
            print(f'  Created: {metadata.created_at}')
            print(f'  Last Rotated: {metadata.last_rotated}')
            print(f'  Rotation Count: {metadata.rotation_count}')

    except Exception as e:
        print(f'❌ Failed to get info: {e}')
        sys.exit(1)


def cmd_migrate(args):
    """迁移密钥"""
    try:
        # 从环境变量读取当前密钥
        current_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')

        if not current_key:
            print('❌ BLOCKCHAIN_PRIVATE_KEY not set in environment')
            sys.exit(1)

        # 验证当前密钥
        manager = KeyManager(key_source=KeySource.ENVIRONMENT)
        manager._private_key = current_key

        if not manager.validate_key():
            print('❌ Current key is invalid')
            sys.exit(1)

        print(f'Current key: {manager.mask_key(current_key)}')
        print(f'Current address: {manager.get_public_address()}')

        # 创建加密文件
        file_manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.output,
            encryption_password=args.password
        )

        file_manager.save_encrypted_key(current_key, args.output)
        print(f'✅ Key migrated to encrypted file: {args.output}')

        # 验证迁移
        verify_manager = KeyManager(
            key_source=KeySource.ENCRYPTED_FILE,
            key_file_path=args.output,
            encryption_password=args.password
        )

        migrated_key = verify_manager.get_private_key()
        if migrated_key == current_key:
            print('✅ Migration verified successfully')
        else:
            print('❌ Migration verification failed')
            sys.exit(1)

    except Exception as e:
        print(f'❌ Migration failed: {e}')
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Nautilus Key Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a new key
  python key_manager_cli.py generate --show-full

  # Encrypt a key
  python key_manager_cli.py encrypt --key 0x123... --password mypass --output key.json

  # Decrypt a key
  python key_manager_cli.py decrypt --input key.json --password mypass

  # Validate a key
  python key_manager_cli.py validate --key 0x123...

  # Rotate a key
  python key_manager_cli.py rotate --input key.json --password mypass

  # Show key info
  python key_manager_cli.py info --source encrypted_file --input key.json --password mypass

  # Migrate from environment variable
  python key_manager_cli.py migrate --output key.json --password mypass
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # encrypt 命令
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt a private key')
    encrypt_parser.add_argument('--key', required=True, help='Private key to encrypt')
    encrypt_parser.add_argument('--password', required=True, help='Encryption password')
    encrypt_parser.add_argument('--output', required=True, help='Output file path')

    # decrypt 命令
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt a private key')
    decrypt_parser.add_argument('--input', required=True, help='Input file path')
    decrypt_parser.add_argument('--password', required=True, help='Decryption password')
    decrypt_parser.add_argument('--show-full', action='store_true', help='Show full key (dangerous!)')

    # validate 命令
    validate_parser = subparsers.add_parser('validate', help='Validate a private key')
    validate_parser.add_argument('--key', required=True, help='Private key to validate')

    # generate 命令
    generate_parser = subparsers.add_parser('generate', help='Generate a new private key')
    generate_parser.add_argument('--show-full', action='store_true', help='Show full key (dangerous!)')
    generate_parser.add_argument('--output', help='Output file path (optional)')
    generate_parser.add_argument('--password', help='Encryption password (required if --output is set)')

    # rotate 命令
    rotate_parser = subparsers.add_parser('rotate', help='Rotate a private key')
    rotate_parser.add_argument('--input', required=True, help='Input file path')
    rotate_parser.add_argument('--password', required=True, help='Encryption password')
    rotate_parser.add_argument('--new-key', help='New private key (optional, will generate if not provided)')

    # info 命令
    info_parser = subparsers.add_parser('info', help='Show key information')
    info_parser.add_argument('--source', required=True, choices=['environment', 'encrypted_file'], help='Key source')
    info_parser.add_argument('--input', help='Input file path (for encrypted_file source)')
    info_parser.add_argument('--password', help='Decryption password (for encrypted_file source)')

    # migrate 命令
    migrate_parser = subparsers.add_parser('migrate', help='Migrate key from environment variable to encrypted file')
    migrate_parser.add_argument('--output', required=True, help='Output file path')
    migrate_parser.add_argument('--password', required=True, help='Encryption password')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    commands = {
        'encrypt': cmd_encrypt,
        'decrypt': cmd_decrypt,
        'validate': cmd_validate,
        'generate': cmd_generate,
        'rotate': cmd_rotate,
        'info': cmd_info,
        'migrate': cmd_migrate
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
