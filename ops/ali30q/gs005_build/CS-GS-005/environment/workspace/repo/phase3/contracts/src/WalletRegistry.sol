// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title WalletRegistry
 * @notice On-chain registry for Nautilus-issued wallets
 * @dev Tracks which EOA addresses were created by the Nautilus platform.
 *      This is a lightweight registry, NOT a factory that deploys contract wallets.
 */
contract WalletRegistry is Ownable {
    mapping(address => bool) public registeredWallets;
    mapping(address => uint256) public walletToAgentId;
    mapping(uint256 => address) public agentIdToWallet;

    uint256 public totalRegistered;

    event WalletRegistered(address indexed wallet, uint256 indexed agentId, uint256 timestamp);
    event WalletDeactivated(address indexed wallet, uint256 timestamp);

    constructor() Ownable(msg.sender) {}

    /**
     * @dev Register a single wallet for an agent. Only callable by owner.
     * @param wallet The EOA address to register
     * @param agentId The agent ID to associate with this wallet
     */
    function registerWallet(address wallet, uint256 agentId) external onlyOwner {
        require(wallet != address(0), "Invalid address");
        require(!registeredWallets[wallet], "Already registered");
        require(agentIdToWallet[agentId] == address(0), "Agent already has wallet");

        registeredWallets[wallet] = true;
        walletToAgentId[wallet] = agentId;
        agentIdToWallet[agentId] = wallet;
        totalRegistered++;

        emit WalletRegistered(wallet, agentId, block.timestamp);
    }

    /**
     * @dev Register a batch of wallets. Silently skips invalid or duplicate entries.
     * @param wallets Array of EOA addresses
     * @param agentIds Array of agent IDs (must match wallets length)
     */
    function registerBatch(address[] calldata wallets, uint256[] calldata agentIds) external onlyOwner {
        require(wallets.length == agentIds.length, "Length mismatch");
        require(wallets.length <= 100, "Batch too large");

        for (uint256 i = 0; i < wallets.length; i++) {
            if (
                !registeredWallets[wallets[i]] &&
                wallets[i] != address(0) &&
                agentIdToWallet[agentIds[i]] == address(0)
            ) {
                registeredWallets[wallets[i]] = true;
                walletToAgentId[wallets[i]] = agentIds[i];
                agentIdToWallet[agentIds[i]] = wallets[i];
                totalRegistered++;
                emit WalletRegistered(wallets[i], agentIds[i], block.timestamp);
            }
        }
    }

    /**
     * @dev Deactivate a registered wallet. Does not remove agent mapping.
     * @param wallet The wallet address to deactivate
     */
    function deactivateWallet(address wallet) external onlyOwner {
        require(registeredWallets[wallet], "Not registered");
        registeredWallets[wallet] = false;
        emit WalletDeactivated(wallet, block.timestamp);
    }

    /**
     * @dev Check if a wallet is registered and active
     */
    function isRegistered(address wallet) external view returns (bool) {
        return registeredWallets[wallet];
    }

    /**
     * @dev Get the agent ID for a registered wallet
     */
    function getAgentId(address wallet) external view returns (uint256) {
        require(registeredWallets[wallet], "Not registered");
        return walletToAgentId[wallet];
    }

    /**
     * @dev Get the wallet address for an agent ID
     */
    function getWallet(uint256 agentId) external view returns (address) {
        return agentIdToWallet[agentId];
    }
}
