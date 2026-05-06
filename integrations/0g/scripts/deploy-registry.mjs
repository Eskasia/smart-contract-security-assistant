import { readFileSync } from "node:fs";
import { ethers } from "ethers";
import solc from "solc";

const DEFAULT_ADDRESS_BASE = "https://www.0gscan.com/address/";

function env(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

function normalizeBaseUrl(value) {
  return value.endsWith("/") ? value : `${value}/`;
}

function compileRegistry() {
  const source = readFileSync(new URL("../contracts/AuditProofRegistry.sol", import.meta.url), "utf-8");
  const input = {
    language: "Solidity",
    sources: { "AuditProofRegistry.sol": { content: source } },
    settings: { outputSelection: { "*": { "*": ["abi", "evm.bytecode"] } } },
  };
  const compiled = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = compiled.errors?.filter((error) => error.severity === "error") ?? [];
  if (errors.length > 0) {
    throw new Error(errors.map((error) => error.formattedMessage).join("\n"));
  }

  const contract = compiled.contracts?.["AuditProofRegistry.sol"]?.AuditProofRegistry;
  if (!contract?.abi || !contract?.evm?.bytecode?.object) {
    throw new Error("AuditProofRegistry compile output is missing ABI or bytecode");
  }
  return contract;
}

const contract = compileRegistry();
const provider = new ethers.JsonRpcProvider(env("ZERO_G_RPC_URL"));
const wallet = new ethers.Wallet(env("ZERO_G_PRIVATE_KEY"), provider);
const factory = new ethers.ContractFactory(contract.abi, contract.evm.bytecode.object, wallet);
const deployed = await factory.deploy();
await deployed.waitForDeployment();

const address = await deployed.getAddress();
if (!ethers.isAddress(address)) {
  throw new Error(`Invalid deployed registry address: ${address}`);
}

const addressBase = normalizeBaseUrl(process.env.ZERO_G_EXPLORER_ADDRESS_BASE ?? DEFAULT_ADDRESS_BASE);
console.log(JSON.stringify({ registry_address: address, explorer_link: `${addressBase}${address}` }, null, 2));
