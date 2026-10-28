const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("IdentityContract", function () {
  let identityContract;
  let owner;
  let user1;
  let user2;
  let agent1;
  let agent2;

  beforeEach(async function () {
    [owner, user1, user2, agent1, agent2] = await ethers.getSigners();

    // Deploy IdentityContract
    const IdentityContract = await ethers.getContractFactory("IdentityContract");
    identityContract = await IdentityContract.deploy();
    await identityContract.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await identityContract.owner()).to.equal(owner.address);
    });
  });

  describe("User Registration", function () {
    it("Should register a user successfully", async function () {
      const tx = await identityContract.connect(user1).registerUser(
        "Alice",
        "alice@example.com"
      );

      await expect(tx)
        .to.emit(identityContract, "UserRegistered")
        .withArgs(user1.address, "Alice");

      const user = await identityContract.getUser(user1.address);
      expect(user.name).to.equal("Alice");
      expect(user.email).to.equal("alice@example.com");
      expect(user.reputation).to.equal(100); // Default reputation
      expect(user.isRegistered).to.equal(true);
    });

    it("Should fail if user already registered", async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");

      await expect(
        identityContract.connect(user1).registerUser("Alice2", "alice2@example.com")
      ).to.be.revertedWith("User already registered");
    });

    it("Should fail with empty name", async function () {
      await expect(
        identityContract.connect(user1).registerUser("", "alice@example.com")
      ).to.be.revertedWith("Name cannot be empty");
    });

    it("Should fail with empty email", async function () {
      await expect(
        identityContract.connect(user1).registerUser("Alice", "")
      ).to.be.revertedWith("Email cannot be empty");
    });

    it("Should register multiple users", async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");
      await identityContract.connect(user2).registerUser("Bob", "bob@example.com");

      const user1Data = await identityContract.getUser(user1.address);
      const user2Data = await identityContract.getUser(user2.address);

      expect(user1Data.name).to.equal("Alice");
      expect(user2Data.name).to.equal("Bob");
    });
  });

  describe("Agent Registration", function () {
    it("Should register an agent successfully", async function () {
      const tx = await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "AI Agent for data processing",
        agent1.address
      );

      await expect(tx)
        .to.emit(identityContract, "AgentRegistered")
        .withArgs(agent1.address, "AgentX");

      const agent = await identityContract.getAgent(agent1.address);
      expect(agent.name).to.equal("AgentX");
      expect(agent.description).to.equal("AI Agent for data processing");
      expect(agent.owner).to.equal(agent1.address);
      expect(agent.reputation).to.equal(100);
      expect(agent.isRegistered).to.equal(true);
    });

    it("Should fail if agent already registered", async function () {
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description",
        agent1.address
      );

      await expect(
        identityContract.connect(agent1).registerAgent(
          "AgentY",
          "Description2",
          agent1.address
        )
      ).to.be.revertedWith("Agent already registered");
    });

    it("Should fail with empty name", async function () {
      await expect(
        identityContract.connect(agent1).registerAgent(
          "",
          "Description",
          agent1.address
        )
      ).to.be.revertedWith("Name cannot be empty");
    });

    it("Should fail with empty description", async function () {
      await expect(
        identityContract.connect(agent1).registerAgent(
          "AgentX",
          "",
          agent1.address
        )
      ).to.be.revertedWith("Description cannot be empty");
    });

    it("Should register multiple agents", async function () {
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description X",
        agent1.address
      );

      await identityContract.connect(agent2).registerAgent(
        "AgentY",
        "Description Y",
        agent2.address
      );

      const agent1Data = await identityContract.getAgent(agent1.address);
      const agent2Data = await identityContract.getAgent(agent2.address);

      expect(agent1Data.name).to.equal("AgentX");
      expect(agent2Data.name).to.equal("AgentY");
    });

    it("Should allow different owner address", async function () {
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description",
        user1.address // Different owner
      );

      const agent = await identityContract.getAgent(agent1.address);
      expect(agent.owner).to.equal(user1.address);
    });
  });

  describe("Reputation Updates", function () {
    beforeEach(async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description",
        agent1.address
      );
    });

    it("Should update user reputation successfully", async function () {
      const tx = await identityContract.updateReputation(user1.address, 150, true);

      await expect(tx)
        .to.emit(identityContract, "ReputationUpdated")
        .withArgs(user1.address, 150, true);

      const user = await identityContract.getUser(user1.address);
      expect(user.reputation).to.equal(150);
    });

    it("Should update agent reputation successfully", async function () {
      const tx = await identityContract.updateReputation(agent1.address, 200, false);

      await expect(tx)
        .to.emit(identityContract, "ReputationUpdated")
        .withArgs(agent1.address, 200, false);

      const agent = await identityContract.getAgent(agent1.address);
      expect(agent.reputation).to.equal(200);
    });

    it("Should fail if not called by owner", async function () {
      await expect(
        identityContract.connect(user1).updateReputation(user1.address, 150, true)
      ).to.be.revertedWithCustomError(identityContract, "OwnableUnauthorizedAccount");
    });

    it("Should handle reputation decrease", async function () {
      await identityContract.updateReputation(user1.address, 50, true);

      const user = await identityContract.getUser(user1.address);
      expect(user.reputation).to.equal(50);
    });

    it("Should handle zero reputation", async function () {
      await identityContract.updateReputation(user1.address, 0, true);

      const user = await identityContract.getUser(user1.address);
      expect(user.reputation).to.equal(0);
    });

    it("Should handle very high reputation", async function () {
      await identityContract.updateReputation(user1.address, 10000, true);

      const user = await identityContract.getUser(user1.address);
      expect(user.reputation).to.equal(10000);
    });
  });

  describe("Registration Check", function () {
    beforeEach(async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description",
        agent1.address
      );
    });

    it("Should return true for registered user", async function () {
      const isRegistered = await identityContract.isRegistered(user1.address, true);
      expect(isRegistered).to.equal(true);
    });

    it("Should return false for unregistered user", async function () {
      const isRegistered = await identityContract.isRegistered(user2.address, true);
      expect(isRegistered).to.equal(false);
    });

    it("Should return true for registered agent", async function () {
      const isRegistered = await identityContract.isRegistered(agent1.address, false);
      expect(isRegistered).to.equal(true);
    });

    it("Should return false for unregistered agent", async function () {
      const isRegistered = await identityContract.isRegistered(agent2.address, false);
      expect(isRegistered).to.equal(false);
    });

    it("Should distinguish between user and agent", async function () {
      // user1 is registered as user, not agent
      const isUserRegistered = await identityContract.isRegistered(user1.address, true);
      const isAgentRegistered = await identityContract.isRegistered(user1.address, false);

      expect(isUserRegistered).to.equal(true);
      expect(isAgentRegistered).to.equal(false);
    });
  });

  describe("Query Functions", function () {
    beforeEach(async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description",
        agent1.address
      );
    });

    it("Should get user data correctly", async function () {
      const user = await identityContract.getUser(user1.address);

      expect(user.name).to.equal("Alice");
      expect(user.email).to.equal("alice@example.com");
      expect(user.reputation).to.equal(100);
      expect(user.isRegistered).to.equal(true);
    });

    it("Should get agent data correctly", async function () {
      const agent = await identityContract.getAgent(agent1.address);

      expect(agent.name).to.equal("AgentX");
      expect(agent.description).to.equal("Description");
      expect(agent.owner).to.equal(agent1.address);
      expect(agent.reputation).to.equal(100);
      expect(agent.isRegistered).to.equal(true);
    });

    it("Should return empty data for unregistered user", async function () {
      const user = await identityContract.getUser(user2.address);

      expect(user.name).to.equal("");
      expect(user.email).to.equal("");
      expect(user.reputation).to.equal(0);
      expect(user.isRegistered).to.equal(false);
    });

    it("Should return empty data for unregistered agent", async function () {
      const agent = await identityContract.getAgent(agent2.address);

      expect(agent.name).to.equal("");
      expect(agent.description).to.equal("");
      expect(agent.owner).to.equal(ethers.ZeroAddress);
      expect(agent.reputation).to.equal(0);
      expect(agent.isRegistered).to.equal(false);
    });
  });

  describe("Edge Cases", function () {
    it("Should handle very long names", async function () {
      const longName = "A".repeat(100);
      await identityContract.connect(user1).registerUser(longName, "alice@example.com");

      const user = await identityContract.getUser(user1.address);
      expect(user.name).to.equal(longName);
    });

    it("Should handle very long emails", async function () {
      const longEmail = "a".repeat(100) + "@example.com";
      await identityContract.connect(user1).registerUser("Alice", longEmail);

      const user = await identityContract.getUser(user1.address);
      expect(user.email).to.equal(longEmail);
    });

    it("Should handle very long descriptions", async function () {
      const longDescription = "D".repeat(500);
      await identityContract.connect(agent1).registerAgent(
        "AgentX",
        longDescription,
        agent1.address
      );

      const agent = await identityContract.getAgent(agent1.address);
      expect(agent.description).to.equal(longDescription);
    });

    it("Should handle special characters in name", async function () {
      const specialName = "Alice-123_@#$";
      await identityContract.connect(user1).registerUser(specialName, "alice@example.com");

      const user = await identityContract.getUser(user1.address);
      expect(user.name).to.equal(specialName);
    });

    it("Should handle unicode characters", async function () {
      const unicodeName = "爱丽丝";
      await identityContract.connect(user1).registerUser(unicodeName, "alice@example.com");

      const user = await identityContract.getUser(user1.address);
      expect(user.name).to.equal(unicodeName);
    });
  });

  describe("Multiple Operations", function () {
    it("Should handle rapid registrations", async function () {
      const signers = await ethers.getSigners();

      for (let i = 0; i < 10; i++) {
        await identityContract.connect(signers[i]).registerUser(
          `User${i}`,
          `user${i}@example.com`
        );
      }

      for (let i = 0; i < 10; i++) {
        const user = await identityContract.getUser(signers[i].address);
        expect(user.name).to.equal(`User${i}`);
      }
    });

    it("Should handle mixed user and agent registrations", async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");
      await identityContract.connect(agent1).registerAgent("AgentX", "Desc", agent1.address);
      await identityContract.connect(user2).registerUser("Bob", "bob@example.com");
      await identityContract.connect(agent2).registerAgent("AgentY", "Desc", agent2.address);

      const user1Data = await identityContract.getUser(user1.address);
      const agent1Data = await identityContract.getAgent(agent1.address);
      const user2Data = await identityContract.getUser(user2.address);
      const agent2Data = await identityContract.getAgent(agent2.address);

      expect(user1Data.isRegistered).to.equal(true);
      expect(agent1Data.isRegistered).to.equal(true);
      expect(user2Data.isRegistered).to.equal(true);
      expect(agent2Data.isRegistered).to.equal(true);
    });

    it("Should handle multiple reputation updates", async function () {
      await identityContract.connect(user1).registerUser("Alice", "alice@example.com");

      await identityContract.updateReputation(user1.address, 120, true);
      await identityContract.updateReputation(user1.address, 150, true);
      await identityContract.updateReputation(user1.address, 200, true);

      const user = await identityContract.getUser(user1.address);
      expect(user.reputation).to.equal(200);
    });
  });

  describe("Gas Optimization", function () {
    it("Should have reasonable gas cost for user registration", async function () {
      const tx = await identityContract.connect(user1).registerUser(
        "Alice",
        "alice@example.com"
      );
      const receipt = await tx.wait();

      // Gas should be reasonable (less than 200k)
      expect(receipt.gasUsed).to.be.lessThan(200000);
    });

    it("Should have reasonable gas cost for agent registration", async function () {
      const tx = await identityContract.connect(agent1).registerAgent(
        "AgentX",
        "Description",
        agent1.address
      );
      const receipt = await tx.wait();

      // Gas should be reasonable (less than 250k)
      expect(receipt.gasUsed).to.be.lessThan(250000);
    });
  });
});
