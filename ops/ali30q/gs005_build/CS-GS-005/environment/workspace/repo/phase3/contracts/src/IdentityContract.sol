// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title IdentityContract
 * @dev 管理智能体的身份和信誉
 */
contract IdentityContract is Ownable {

    // 智能体结构
    struct Agent {
        uint256 agentId;
        address owner;
        string name;
        string description;
        uint256 reputation;
        uint256 createdAt;
    }

    // 状态变量
    uint256 public nextAgentId;
    mapping(uint256 => Agent) public agents;
    mapping(address => uint256) public ownerToAgentId;
    address public taskContract;

    // 事件
    event AgentRegistered(uint256 indexed agentId, address indexed owner, string name);
    event ReputationUpdated(uint256 indexed agentId, uint256 newReputation);

    constructor() Ownable(msg.sender) {
        nextAgentId = 1;
    }

    /**
     * @dev 设置任务合约地址
     */
    function setTaskContract(address _taskContract) external onlyOwner {
        require(_taskContract != address(0), "Invalid address");
        taskContract = _taskContract;
    }

    /**
     * @dev 注册智能体
     */
    function registerAgent(
        string memory name,
        string memory description
    ) external returns (uint256) {
        require(ownerToAgentId[msg.sender] == 0, "Agent already registered");

        uint256 agentId = nextAgentId++;

        agents[agentId] = Agent({
            agentId: agentId,
            owner: msg.sender,
            name: name,
            description: description,
            reputation: 100,  // 初始信誉分数
            createdAt: block.timestamp
        });

        ownerToAgentId[msg.sender] = agentId;

        emit AgentRegistered(agentId, msg.sender, name);
        return agentId;
    }

    /**
     * @dev 更新信誉分数（仅任务合约可调用）
     */
    function updateReputation(uint256 agentId, int256 delta) external {
        require(msg.sender == taskContract, "Not task contract");

        Agent storage agent = agents[agentId];
        require(agent.agentId != 0, "Agent not found");

        // 更新信誉分数（不能低于0）
        if (delta < 0 && uint256(-delta) > agent.reputation) {
            agent.reputation = 0;
        } else {
            agent.reputation = uint256(int256(agent.reputation) + delta);
        }

        emit ReputationUpdated(agentId, agent.reputation);
    }

    /**
     * @dev 查询信誉分数
     */
    function getReputation(uint256 agentId) external view returns (uint256) {
        return agents[agentId].reputation;
    }

    /**
     * @dev 获取智能体详情
     */
    function getAgent(uint256 agentId) external view returns (Agent memory) {
        return agents[agentId];
    }

    /**
     * @dev 通过所有者地址获取智能体ID
     */
    function getAgentIdByOwner(address agentOwner) external view returns (uint256) {
        return ownerToAgentId[agentOwner];
    }
}
