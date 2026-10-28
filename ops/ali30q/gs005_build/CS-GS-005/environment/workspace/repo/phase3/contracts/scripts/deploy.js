/**
 * Deploy Nautilus contracts to Base Sepolia.
 *
 * Usage:
 *   npx hardhat run scripts/deploy.js --network baseSepolia
 *
 * Required env vars:
 *   DEPLOYER_PRIVATE_KEY - deployer wallet private key
 *   BASE_SEPOLIA_RPC     - RPC URL (default: https://sepolia.base.org)
 */
const { ethers } = require("hardhat");

// Base Sepolia USDC faucet token (Circle testnet faucet)
const USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");

  // 1. Deploy RewardContract (5% fee, deployer receives fees initially)
  const RewardContract = await ethers.getContractFactory("RewardContract");
  const reward = await RewardContract.deploy(500, deployer.address);
  await reward.waitForDeployment();
  console.log("RewardContract:", await reward.getAddress());

  // 2. Deploy TaskContract
  const TaskContract = await ethers.getContractFactory("TaskContract");
  const task = await TaskContract.deploy();
  await task.waitForDeployment();
  console.log("TaskContract:", await task.getAddress());

  // 3. Deploy IdentityContract
  const IdentityContract = await ethers.getContractFactory("IdentityContract");
  const identity = await IdentityContract.deploy();
  await identity.waitForDeployment();
  console.log("IdentityContract:", await identity.getAddress());

  // 4. Wire contracts together
  await task.setRewardContract(await reward.getAddress());
  await task.setVerificationEngine(deployer.address); // deployer as verifier for testing
  await task.addSupportedToken(USDC_BASE_SEPOLIA);

  await reward.setTaskContract(await task.getAddress());
  await reward.addSupportedToken(USDC_BASE_SEPOLIA);

  console.log("\nDeployment complete! Contract addresses:");
  console.log(`  TASK_CONTRACT=${await task.getAddress()}`);
  console.log(`  REWARD_CONTRACT=${await reward.getAddress()}`);
  console.log(`  IDENTITY_CONTRACT=${await identity.getAddress()}`);
  console.log(`  USDC_TOKEN=${USDC_BASE_SEPOLIA}`);
  console.log(`  CHAIN=base-sepolia (84532)`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
