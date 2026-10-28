/**
 * TaskContract + RewardContract ERC20 integration tests.
 * Full payment flow: publish → accept → submit → verify → complete → withdraw
 */
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Nautilus ERC20 Payment Flow", function () {
  let taskContract, rewardContract, mockUSDC;
  let owner, publisher, agent, feeRecipient;

  const REWARD = ethers.parseUnits("10", 6); // 10 USDC
  const FEE_BPS = 500; // 5%
  const TIMEOUT = 3600;

  beforeEach(async function () {
    [owner, publisher, agent, feeRecipient] = await ethers.getSigners();

    // Deploy mock USDC
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    mockUSDC = await MockERC20.deploy("USD Coin", "USDC", 6);

    // Deploy core contracts
    const RC = await ethers.getContractFactory("RewardContract");
    rewardContract = await RC.deploy(FEE_BPS, feeRecipient.address);

    const TC = await ethers.getContractFactory("TaskContract");
    taskContract = await TC.deploy();

    // Wire contracts together
    await taskContract.setRewardContract(await rewardContract.getAddress());
    await taskContract.setVerificationEngine(owner.address);
    await taskContract.addSupportedToken(await mockUSDC.getAddress());
    await rewardContract.setTaskContract(await taskContract.getAddress());
    await rewardContract.addSupportedToken(await mockUSDC.getAddress());

    // Fund publisher
    await mockUSDC.mint(publisher.address, ethers.parseUnits("1000", 6));
  });

  it("full flow: publish → accept → submit → verify → complete → withdraw", async function () {
    const usdcAddr = await mockUSDC.getAddress();
    const taskAddr = await taskContract.getAddress();

    // Publish
    await mockUSDC.connect(publisher).approve(taskAddr, REWARD);
    await taskContract.connect(publisher).publishTask(
      "Label 100 texts", '{"items":[]}', "labels", REWARD, usdcAddr, 1, TIMEOUT
    );
    expect(await mockUSDC.balanceOf(taskAddr)).to.equal(REWARD);

    // Accept
    await taskContract.connect(agent).acceptTask(1);

    // Submit
    await taskContract.connect(agent).submitResult(1, '{"labels":[]}');

    // Verify
    await taskContract.verifyResult(1, true);

    // Complete → rewards distributed
    await taskContract.completeTask(1);

    // Check agent balance (95% of 10 USDC = 9.5 USDC)
    const expectedAgent = REWARD - (REWARD * BigInt(FEE_BPS) / 10000n);
    expect(await rewardContract.getBalance(agent.address, usdcAddr)).to.equal(expectedAgent);

    // Check fee (5% = 0.5 USDC)
    const expectedFee = REWARD * BigInt(FEE_BPS) / 10000n;
    expect(await mockUSDC.balanceOf(feeRecipient.address)).to.equal(expectedFee);

    // Withdraw
    await rewardContract.connect(agent).withdrawReward(usdcAddr);
    expect(await mockUSDC.balanceOf(agent.address)).to.equal(expectedAgent);
  });

  it("refund on timeout", async function () {
    const usdcAddr = await mockUSDC.getAddress();
    const taskAddr = await taskContract.getAddress();
    const before = await mockUSDC.balanceOf(publisher.address);

    await mockUSDC.connect(publisher).approve(taskAddr, REWARD);
    await taskContract.connect(publisher).publishTask(
      "test", "", "", REWARD, usdcAddr, 1, 1
    );

    await ethers.provider.send("evm_increaseTime", [2]);
    await ethers.provider.send("evm_mine");

    await taskContract.handleTimeout(1);
    expect(await mockUSDC.balanceOf(publisher.address)).to.equal(before);
  });

  it("reject unsupported token", async function () {
    const fake = ethers.Wallet.createRandom().address;
    await expect(
      taskContract.connect(publisher).publishTask("x", "", "", REWARD, fake, 1, TIMEOUT)
    ).to.be.revertedWithCustomError(taskContract, "UnsupportedToken");
  });
});
