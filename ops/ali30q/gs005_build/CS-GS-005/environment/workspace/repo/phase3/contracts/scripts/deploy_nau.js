const hre = require("hardhat");

async function main() {
  console.log("Deploying NautilusToken to", hre.network.name);

  const [deployer] = await hre.ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Balance:", hre.ethers.formatEther(balance), "ETH");

  if (balance === 0n) {
    throw new Error("Deployer has no ETH. Get testnet ETH from faucet first.");
  }

  const NautilusToken = await hre.ethers.getContractFactory("NautilusToken");
  const token = await NautilusToken.deploy();
  await token.waitForDeployment();

  const address = await token.getAddress();
  console.log("\n✅ NautilusToken deployed to:", address);
  console.log("\nAdd to server .env:");
  console.log("  NAU_TOKEN_ADDRESS=" + address);
  console.log("  BLOCKCHAIN_PRIVATE_KEY=0x<deployer_private_key>");
  console.log("\nVerify on Basescan:");
  console.log("  https://sepolia.basescan.org/address/" + address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
