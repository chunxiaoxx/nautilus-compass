/**
 * E2E Payment Flow Test on Base Sepolia
 *
 * Flow: Mint USDC -> Approve -> Publish Task -> Accept -> Submit -> Verify -> Complete -> Withdraw
 *
 * Uses deployed contracts on Base Sepolia testnet.
 */
const { ethers } = require("hardhat");

const TASK_CONTRACT = "0x69f258D20e5549236B5B68A33F26302B331379B6";
const REWARD_CONTRACT = "0x1f4d8E8Bdfc0323c5a684452071fa71129d4D8A3";
const USDC_ADDRESS = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";

// Minimal ERC20 ABI
const ERC20_ABI = [
  "function balanceOf(address) view returns (uint256)",
  "function approve(address spender, uint256 amount) returns (bool)",
  "function allowance(address owner, address spender) view returns (uint256)",
  "function decimals() view returns (uint8)",
  "function symbol() view returns (string)",
];

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("=== Nautilus E2E Payment Test (Base Sepolia) ===\n");
  console.log("Tester:", deployer.address);

  // Connect to contracts
  const task = await ethers.getContractAt("TaskContract", TASK_CONTRACT);
  const reward = await ethers.getContractAt("RewardContract", REWARD_CONTRACT);
  const usdc = new ethers.Contract(USDC_ADDRESS, ERC20_ABI, deployer);

  // Check USDC balance
  const decimals = await usdc.decimals();
  const symbol = await usdc.symbol();
  const balance = await usdc.balanceOf(deployer.address);
  console.log(`USDC Balance: ${ethers.formatUnits(balance, decimals)} ${symbol}`);

  if (balance === 0n) {
    console.log("\n** No USDC balance! **");
    console.log("Get test USDC from Circle faucet: https://faucet.circle.com/");
    console.log("Select 'Base Sepolia' network and enter your address.");
    console.log("Then re-run this script.\n");
    return;
  }

  const rewardAmount = ethers.parseUnits("1", decimals); // 1 USDC

  // Step 1: Approve USDC
  console.log("\n--- Step 1: Approve USDC ---");
  let tx = await usdc.approve(TASK_CONTRACT, rewardAmount);
  await tx.wait();
  console.log("Approved 1 USDC to TaskContract, tx:", tx.hash);

  const allowance = await usdc.allowance(deployer.address, TASK_CONTRACT);
  console.log("Allowance:", ethers.formatUnits(allowance, decimals), symbol);

  // Step 2: Publish task
  console.log("\n--- Step 2: Publish Task ---");
  tx = await task.publishTask(
    "E2E test: classify sentiment",
    '{"text": "Nautilus is amazing!"}',
    "positive",
    rewardAmount,
    USDC_ADDRESS,
    1, // DATA type
    3600 // 1 hour timeout
  );
  const receipt = await tx.wait();
  console.log("Task published, tx:", tx.hash);

  // Get task ID from event
  const publishEvent = receipt.logs.find(log => {
    try {
      return task.interface.parseLog(log)?.name === "TaskPublished";
    } catch { return false; }
  });
  const taskId = publishEvent
    ? task.interface.parseLog(publishEvent).args[0]
    : 1n;
  console.log("Task ID:", taskId.toString());

  // Check USDC moved to contract
  const contractBalance = await usdc.balanceOf(TASK_CONTRACT);
  console.log("TaskContract USDC balance:", ethers.formatUnits(contractBalance, decimals));

  // Step 3: Accept task (deployer acts as agent too)
  console.log("\n--- Step 3: Accept Task ---");
  tx = await task.acceptTask(taskId);
  await tx.wait();
  console.log("Task accepted, tx:", tx.hash);

  // Step 4: Submit result
  console.log("\n--- Step 4: Submit Result ---");
  tx = await task.submitResult(taskId, "positive");
  await tx.wait();
  console.log("Result submitted, tx:", tx.hash);

  // Step 5: Verify result (deployer is verification engine)
  console.log("\n--- Step 5: Verify Result ---");
  tx = await task.verifyResult(taskId, true);
  await tx.wait();
  console.log("Result verified, tx:", tx.hash);

  // Step 6: Complete task (triggers reward distribution)
  console.log("\n--- Step 6: Complete Task ---");
  tx = await task.completeTask(taskId);
  await tx.wait();
  console.log("Task completed, tx:", tx.hash);

  // Check reward balance
  const rewardBalance = await reward.getBalance(deployer.address, USDC_ADDRESS);
  console.log("Agent reward balance:", ethers.formatUnits(rewardBalance, decimals), symbol);

  // Step 7: Withdraw reward
  console.log("\n--- Step 7: Withdraw Reward ---");
  tx = await reward.withdrawReward(USDC_ADDRESS);
  await tx.wait();
  console.log("Reward withdrawn, tx:", tx.hash);

  // Final balances
  const finalBalance = await usdc.balanceOf(deployer.address);
  const finalRewardBalance = await reward.getBalance(deployer.address, USDC_ADDRESS);
  console.log("\n=== Final State ===");
  console.log("USDC balance:", ethers.formatUnits(finalBalance, decimals), symbol);
  console.log("Reward balance:", ethers.formatUnits(finalRewardBalance, decimals), symbol);
  console.log("Fee deducted:", ethers.formatUnits(balance - finalBalance, decimals), symbol, "(5% platform fee)");
  console.log("\nE2E Payment Flow: SUCCESS");
}

main().catch((error) => {
  console.error("\nE2E Test FAILED:", error.message || error);
  process.exitCode = 1;
});
