"""
Memory Module - EverMemOS 记忆系统集成
预留接口，用于集成 EverMemOS
"""
from typing import Dict, List, Optional
import httpx


class MemoryClient:
    """EverMemOS 客户端"""

    def __init__(self, base_url: str = "http://localhost:1995"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    async def store_memory(self, message_id: str, sender: str, content: str, create_time: str) -> Dict:
        """存储记忆"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/memories",
                json={
                    "message_id": message_id,
                    "create_time": create_time,
                    "sender": sender,
                    "content": content
                }
            )
            return response.json()

    async def search_memory(self, query: str, user_id: str, memory_types: List[str] = None) -> Dict:
        """搜索记忆"""
        if memory_types is None:
            memory_types = ["episodic_memory"]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/memories/search",
                json={
                    "query": query,
                    "user_id": user_id,
                    "memory_types": memory_types,
                    "retrieve_method": "hybrid"
                }
            )
            return response.json()

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False


__all__ = ["MemoryClient"]
