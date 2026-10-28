/**
 * Deploy WalletRegistry contract to Base Sepolia.
 *
 * Usage:
 *   npx hardhat run scripts/deploy_wallet_registry.js --network baseSepolia
 *
 * Required env vars:
 *   DEPLOYER_PRIVATE_KEY - deployer wallet private key
 *   BASE_SEPOLIA_RPC     - RPC URL (default: https://sepolia.base.org)
 */
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying WalletRegistry with:", deployer.address);
  console.log(
    "Balance:",
    ethers.formatEther(await ethers.provider.getBalance(deployer.address)),
    "ETH"
  );

  // Deploy WalletRegistry
  const WalletRegistry = await ethers.getContractFactory("WalletRegistry");
  const registry = await WalletRegistry.deploy();
  await registry.waitForDeployment();

  const registryAddress = await registry.getAddress();
  console.log("WalletRegistry:", registryAddress);

  // Save ABI to backend
  const artifact = await artifacts.readArtifact("WalletRegistry");
  const abiDir = path.resolve(
    __dirname,
    "../../backend/blockchain/abi"
  );

  if (!fs.existsSync(abiDir)) {
    fs.mkdirSync(abiDir, { recursive: true });
  }

  fs.writeFileSync(
    path.join(abiDir, "WalletRegistry.json"),
    JSON.stringify(artifact.abi, null, 2)
  );
  console.log("ABI saved to backend/blockchain/abi/WalletRegistry.json");

  console.log("\nDeployment complete!");
  console.log(`  WALLET_REGISTRY=${registryAddress}`);
  console.log(`  CHAIN=base-sepolia (84532)`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
