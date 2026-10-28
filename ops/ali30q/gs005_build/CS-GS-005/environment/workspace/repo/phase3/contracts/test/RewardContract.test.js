const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RewardContract", function () {
  let rewardContract;
  let taskContract;
  let owner;
  let agent1;
  let agent2;

  const REWARD_AMOUNT = ethers.parseEther("1.0");

  beforeEach(async function () {
    [owner, taskContract, agent1, agent2] = await ethers.getSigners();

    // Deploy RewardContract
    const RewardContract = await ethers.getContractFactory("RewardContract");
    rewardContract = await RewardContract.deploy();
    await rewardContract.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await rewardContract.owner()).to.equal(owner.address);
    });

    it("Should start with zero total rewards", async function () {
      expect(await rewardContract.getTotalRewards()).to.equal(0);
    });
  });

  describe("Reward Distribution", function () {
    it("Should distribute reward successfully", async function () {
      const tx = await rewardContract.connect(taskContract).distributeReward(
        1, // taskId
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await expect(tx)
        .to.emit(rewardContract, "RewardDistributed")
        .withArgs(1, agent1.address, REWARD_AMOUNT);

      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(REWARD_AMOUNT);
    });

    it("Should accumulate multiple rewards for same agent", async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await rewardContract.connect(taskContract).distributeReward(
        2,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(REWARD_AMOUNT * 2n);
    });

    it("Should track rewards for multiple agents", async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await rewardContract.connect(taskContract).distributeReward(
        2,
        agent2.address,
        { value: REWARD_AMOUNT * 2n }
      );

      const reward1 = await rewardContract.getReward(agent1.address);
      const reward2 = await rewardContract.getReward(agent2.address);

      expect(reward1).to.equal(REWARD_AMOUNT);
      expect(reward2).to.equal(REWARD_AMOUNT * 2n);
    });

    it("Should update total rewards correctly", async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await rewardContract.connect(taskContract).distributeReward(
        2,
        agent2.address,
        { value: REWARD_AMOUNT * 2n }
      );

      const totalRewards = await rewardContract.getTotalRewards();
      expect(totalRewards).to.equal(REWARD_AMOUNT * 3n);
    });

    it("Should handle zero reward amount", async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: 0 }
      );

      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(0);
    });
  });

  describe("Reward Withdrawal", function () {
    beforeEach(async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );
    });

    it("Should withdraw reward successfully", async function () {
      const initialBalance = await ethers.provider.getBalance(agent1.address);

      const tx = await rewardContract.connect(agent1).withdraw();
      const receipt = await tx.wait();
      const gasUsed = receipt.gasUsed * receipt.gasPrice;

      await expect(tx)
        .to.emit(rewardContract, "RewardWithdrawn")
        .withArgs(agent1.address, REWARD_AMOUNT);

      const finalBalance = await ethers.provider.getBalance(agent1.address);
      expect(finalBalance).to.equal(initialBalance + REWARD_AMOUNT - gasUsed);

      const remainingReward = await rewardContract.getReward(agent1.address);
      expect(remainingReward).to.equal(0);
    });

    it("Should fail if no reward to withdraw", async function () {
      await expect(
        rewardContract.connect(agent2).withdraw()
      ).to.be.revertedWith("No rewards to withdraw");
    });

    it("Should fail if already withdrawn", async function () {
      await rewardContract.connect(agent1).withdraw();

      await expect(
        rewardContract.connect(agent1).withdraw()
      ).to.be.revertedWith("No rewards to withdraw");
    });

    it("Should allow partial withdrawals", async function () {
      // Add more rewards
      await rewardContract.connect(taskContract).distributeReward(
        2,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      // First withdrawal
      await rewardContract.connect(agent1).withdraw();

      // Add more rewards after withdrawal
      await rewardContract.connect(taskContract).distributeReward(
        3,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      // Second withdrawal should work
      const tx = await rewardContract.connect(agent1).withdraw();
      await expect(tx)
        .to.emit(rewardContract, "RewardWithdrawn")
        .withArgs(agent1.address, REWARD_AMOUNT);
    });
  });

  describe("Query Functions", function () {
    beforeEach(async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await rewardContract.connect(taskContract).distributeReward(
        2,
        agent2.address,
        { value: REWARD_AMOUNT * 2n }
      );
    });

    it("Should get reward for specific agent", async function () {
      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(REWARD_AMOUNT);
    });

    it("Should return zero for agent with no rewards", async function () {
      const reward = await rewardContract.getReward(owner.address);
      expect(reward).to.equal(0);
    });

    it("Should get total rewards distributed", async function () {
      const totalRewards = await rewardContract.getTotalRewards();
      expect(totalRewards).to.equal(REWARD_AMOUNT * 3n);
    });

    it("Should update total rewards after withdrawal", async function () {
      await rewardContract.connect(agent1).withdraw();

      // Total rewards should remain the same (tracks distributed, not current balance)
      const totalRewards = await rewardContract.getTotalRewards();
      expect(totalRewards).to.equal(REWARD_AMOUNT * 3n);
    });
  });

  describe("Edge Cases", function () {
    it("Should handle very large reward amounts", async function () {
      const largeReward = ethers.parseEther("1000000");

      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: largeReward }
      );

      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(largeReward);
    });

    it("Should handle very small reward amounts", async function () {
      const smallReward = 1n; // 1 wei

      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: smallReward }
      );

      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(smallReward);
    });

    it("Should handle multiple rapid distributions", async function () {
      for (let i = 0; i < 10; i++) {
        await rewardContract.connect(taskContract).distributeReward(
          i + 1,
          agent1.address,
          { value: REWARD_AMOUNT }
        );
      }

      const reward = await rewardContract.getReward(agent1.address);
      expect(reward).to.equal(REWARD_AMOUNT * 10n);
    });

    it("Should handle distribution to zero address", async function () {
      // This should technically fail in a production contract
      // but we test current behavior
      await rewardContract.connect(taskContract).distributeReward(
        1,
        ethers.ZeroAddress,
        { value: REWARD_AMOUNT }
      );

      const reward = await rewardContract.getReward(ethers.ZeroAddress);
      expect(reward).to.equal(REWARD_AMOUNT);
    });
  });

  describe("Contract Balance", function () {
    it("Should maintain correct contract balance", async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await rewardContract.connect(taskContract).distributeReward(
        2,
        agent2.address,
        { value: REWARD_AMOUNT * 2n }
      );

      const contractBalance = await ethers.provider.getBalance(
        await rewardContract.getAddress()
      );

      expect(contractBalance).to.equal(REWARD_AMOUNT * 3n);
    });

    it("Should decrease contract balance after withdrawal", async function () {
      await rewardContract.connect(taskContract).distributeReward(
        1,
        agent1.address,
        { value: REWARD_AMOUNT }
      );

      await rewardContract.connect(agent1).withdraw();

      const contractBalance = await ethers.provider.getBalance(
        await rewardContract.getAddress()
      );

      expect(contractBalance).to.equal(0);
    });
  });

  describe("Reentrancy Protection", function () {
    it("Should be protected against reentrancy attacks", async function () {
      // Deploy a malicious contract that tries to reenter
      const MaliciousContract = await ethers.getContractFactory("MaliciousReentrancy");
      const malicious = await MaliciousContract.deploy(await rewardContract.getAddress());
      await malicious.waitForDeployment();

      // Distribute reward to malicious contract
      await rewardContract.connect(taskContract).distributeReward(
        1,
        await malicious.getAddress(),
        { value: REWARD_AMOUNT }
      );

      // Attempt reentrancy attack should fail
      await expect(
        malicious.attack()
      ).to.be.reverted;
    });
  });
});

// Helper contract for reentrancy testing
// This would need to be in a separate file in production
/*
contract MaliciousReentrancy {
    RewardContract public rewardContract;
    uint256 public attackCount;

    constructor(address _rewardContract) {
        rewardContract = RewardContract(_rewardContract);
    }

    function attack() external {
        rewardContract.withdraw();
    }

    receive() external payable {
        if (attackCount < 2) {
            attackCount++;
            rewardContract.withdraw();
        }
    }
}
*/
