/**
 * Deploy remaining Nautilus contracts (TaskContract, IdentityContract)
 * and wire them together with already-deployed RewardContract.
 */
const { ethers } = require("hardhat");

const USDC_BASE_SEPOLIA = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";
const REWARD_CONTRACT = "0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with:", deployer.address);
  console.log("Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");

  // RewardContract already deployed
  const reward = await ethers.getContractAt("RewardContract", REWARD_CONTRACT);
  console.log("RewardContract (existing):", REWARD_CONTRACT);

  // 1. Deploy TaskContract
  console.log("\nDeploying TaskContract...");
  const TaskContract = await ethers.getContractFactory("TaskContract");
  const task = await TaskContract.deploy();
  await task.waitForDeployment();
  const taskAddr = await task.getAddress();
  console.log("TaskContract:", taskAddr);

  // 2. Deploy IdentityContract
  console.log("Deploying IdentityContract...");
  const IdentityContract = await ethers.getContractFactory("IdentityContract");
  const identity = await IdentityContract.deploy();
  await identity.waitForDeployment();
  const identityAddr = await identity.getAddress();
  console.log("IdentityContract:", identityAddr);

  // 3. Wire contracts
  console.log("\nWiring contracts...");
  let tx;

  tx = await task.setRewardContract(REWARD_CONTRACT);
  await tx.wait();
  console.log("  TaskContract.setRewardContract done");

  tx = await task.setVerificationEngine(deployer.address);
  await tx.wait();
  console.log("  TaskContract.setVerificationEngine done");

  tx = await task.addSupportedToken(USDC_BASE_SEPOLIA);
  await tx.wait();
  console.log("  TaskContract.addSupportedToken(USDC) done");

  tx = await reward.setTaskContract(taskAddr);
  await tx.wait();
  console.log("  RewardContract.setTaskContract done");

  tx = await reward.addSupportedToken(USDC_BASE_SEPOLIA);
  await tx.wait();
  console.log("  RewardContract.addSupportedToken(USDC) done");

  console.log("\n========== Deployment Complete ==========");
  console.log(`TASK_CONTRACT_ADDRESS=${taskAddr}`);
  console.log(`REWARD_CONTRACT_ADDRESS=${REWARD_CONTRACT}`);
  console.log(`IDENTITY_CONTRACT_ADDRESS=${identityAddr}`);
  console.log(`USDC_TOKEN=${USDC_BASE_SEPOLIA}`);
  console.log(`CHAIN=base-sepolia (84532)`);
  console.log(`DEPLOYER=${deployer.address}`);
  console.log("==========================================");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
