"""
Blockchain Module - 区块链集成
预留接口，用于未来集成区块链
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib
import time


@dataclass
class Block:
    """区块"""
    index: int
    timestamp: float
    data: Dict
    previous_hash: str
    hash: str
    nonce: int = 0


class Blockchain:
    """简单区块链实现"""

    def __init__(self):
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """创建创世区块"""
        genesis = Block(
            index=0,
            timestamp=time.time(),
            data={"message": "Genesis Block"},
            previous_hash="0",
            hash="",
            nonce=0
        )
        genesis.hash = self.calculate_hash(genesis)
        self.chain.append(genesis)

    def calculate_hash(self, block: Block) -> str:
        """计算区块哈希"""
        data = f"{block.index}{block.timestamp}{block.data}{block.previous_hash}{block.nonce}"
        return hashlib.sha256(data.encode()).hexdigest()

    def get_latest_block(self) -> Block:
        """获取最新区块"""
        return self.chain[-1]

    def add_block(self, data: Dict) -> Block:
        """添加新区块"""
        previous_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            previous_hash=previous_block.hash,
            hash="",
            nonce=0
        )
        new_block.hash = self.calculate_hash(new_block)
        self.chain.append(new_block)
        return new_block

    def is_valid(self) -> bool:
        """验证区块链"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != self.calculate_hash(current):
                return False

            if current.previous_hash != previous.hash:
                return False

        return True


__all__ = ["Block", "Blockchain"]
