#\!/usr/bin/env python3
"""创建Nautilus系统测试数据"""
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import random

from models.database import Base, User, Agent, Task, TaskType, TaskStatus

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nautilus_user:nautilus_pass@localhost:5432/nautilus_phase3")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_test_users(session):
    print("\n=== 创建测试用户 ===")
    test_users = [
        {"username": "alice_dev", "email": "alice@nautilus.test", "password": "Test123\!@#",
         "wallet_address": "0x1234567890123456789012345678901234567890", "is_admin": False},
        {"username": "bob_researcher", "email": "bob@nautilus.test", "password": "Test123\!@#",
         "wallet_address": "0x2345678901234567890123456789012345678901", "is_admin": False},
        {"username": "charlie_analyst", "email": "charlie@nautilus.test", "password": "Test123\!@#",
         "wallet_address": "0x3456789012345678901234567890123456789012", "is_admin": False},
        {"username": "diana_admin", "email": "diana@nautilus.test", "password": "Admin123\!@#",
         "wallet_address": "0x4567890123456789012345678901234567890123", "is_admin": True},
        {"username": "eve_designer", "email": "eve@nautilus.test", "password": "Test123\!@#",
         "wallet_address": "0x5678901234567890123456789012345678901234", "is_admin": False}
    ]
    created_users = []
    for user_data in test_users:
        existing_user = session.query(User).filter(
            (User.username == user_data["username"]) | (User.email == user_data["email"])
        ).first()
        if existing_user:
            print(f"  ⚠ 用户 {user_data['username']} 已存在，跳过")
            created_users.append(existing_user)
            continue
        user = User(
            username=user_data["username"], email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            wallet_address=user_data["wallet_address"],
            is_admin=user_data["is_admin"], is_active=True
        )
        session.add(user)
        created_users.append(user)
        print(f"  ✓ 创建用户: {user_data['username']} ({user_data['email']})")
        print(f"    密码: {user_data['password']}")
    session.commit()
    print(f"\n✓ 成功创建用户")
    return created_users
