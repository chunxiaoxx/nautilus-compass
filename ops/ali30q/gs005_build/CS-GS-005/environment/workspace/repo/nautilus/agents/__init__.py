"""
Agents Module - CrewAI 多智能体协作
预留接口，用于集成 CrewAI
"""
from typing import List, Dict, Optional


class AgentInterface:
    """智能体接口"""

    def __init__(self, agent_id: str, role: str):
        self.agent_id = agent_id
        self.role = role

    async def execute(self, task: Dict) -> Dict:
        """执行任务"""
        raise NotImplementedError


class CrewManager:
    """Crew 管理器"""

    def __init__(self):
        self.agents: Dict[str, AgentInterface] = {}
        self.crews: Dict[str, List[str]] = {}

    def register_agent(self, agent: AgentInterface):
        """注册智能体"""
        self.agents[agent.agent_id] = agent

    def create_crew(self, crew_id: str, agent_ids: List[str]):
        """创建 Crew"""
        self.crews[crew_id] = agent_ids

    async def execute_crew(self, crew_id: str, task: Dict) -> List[Dict]:
        """执行 Crew 任务"""
        agent_ids = self.crews.get(crew_id, [])
        results = []
        for agent_id in agent_ids:
            agent = self.agents.get(agent_id)
            if agent:
                result = await agent.execute(task)
                results.append(result)
        return results


__all__ = ["AgentInterface", "CrewManager"]
