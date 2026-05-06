import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { ethers } from "ethers";
import solc from "solc";

const DEFAULT_TX_BASE = "https://www.0gscan.com/tx/";
const DEFAULT_ADDRESS_BASE = "https://www.0gscan.com/address/";
const HASH_PATTERN = /^0x[0-9a-fA-F]{64}$/;
const SHA256_PATTERN = /^[0-9a-fA-F]{64}$/;

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

function requireHash(value, label) {
  if (typeof value !== "string" || !HASH_PATTERN.test(value)) {
    throw new Error(`${label} must be a 0x-prefixed 32-byte hex string`);
  }
  return value;
}

function requireSha256(value, label) {
  if (typeof value !== "string" || !SHA256_PATTERN.test(value)) {
    throw new Error(`${label} must be a 64-character sha256 hex string`);
  }
  return `0x${value}`;
}

function requireContractId(value) {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error("artifact.contract_id is required");
  }
  return value;
}

function requireAddress(value, label) {
  if (!ethers.isAddress(value)) {
    throw new Error(`${label} must be a valid 20-byte EVM address`);
  }
  return ethers.getAddress(value);
}

function scoreToBps(value, label) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 100) {
    throw new Error(`${label} must be a number from 0 to 100`);
  }
  return Math.round(value * 100);
}

function securityScoreBps(proof) {
  if (proof.artifact?.security_score_bps !== undefined && proof.artifact.security_score_bps !== null) {
    if (
      typeof proof.artifact.security_score_bps !== "number" ||
      !Number.isInteger(proof.artifact.security_score_bps) ||
      proof.artifact.security_score_bps < 0 ||
      proof.artifact.security_score_bps > 10000
    ) {
      throw new Error("artifact.security_score_bps must be an integer from 0 to 10000");
    }
    return proof.artifact.security_score_bps;
  }
  if (proof.artifact?.security_score !== undefined && proof.artifact.security_score !== null) {
    return scoreToBps(proof.artifact.security_score, "artifact.security_score");
  }
  if (proof.report?.security_score !== undefined && proof.report.security_score !== null) {
    return scoreToBps(proof.report.security_score, "report.security_score");
  }
  return 10000;
}

function reportHash(proof) {
  const artifactHash = requireSha256(proof.artifact?.report_sha256, "artifact.report_sha256");
  if (proof.report?.sha256 !== undefined && proof.report.sha256 !== null) {
    const reportHashValue = requireSha256(proof.report.sha256, "report.sha256");
    if (reportHashValue !== artifactHash) {
      throw new Error("report.sha256 must match artifact.report_sha256");
    }
  }
  return artifactHash;
}

function compileRegistryAbi() {
  const source = readFileSync(new URL("../contracts/AuditProofRegistry.sol", import.meta.url), "utf-8");
  const input = {
    language: "Solidity",
    sources: { "AuditProofRegistry.sol": { content: source } },
    settings: { outputSelection: { "*": { "*": ["abi"] } } },
  };
  const compiled = JSON.parse(solc.compile(JSON.stringify(input)));
  const errors = compiled.errors?.filter((error) => error.severity === "error") ?? [];
  if (errors.length > 0) {
    throw new Error(errors.map((error) => error.formattedMessage).join("\n"));
  }

  const abi = compiled.contracts?.["AuditProofRegistry.sol"]?.AuditProofRegistry?.abi;
  if (!abi) {
    throw new Error("AuditProofRegistry compile output is missing ABI");
  }
  return abi;
}

const inputPath = process.argv[2] ?? "submission-proof.json";
if (!existsSync(inputPath)) {
  throw new Error("Usage: npm run register -- <submission-proof.json>");
}

const proof = JSON.parse(readFileSync(inputPath, "utf-8"));
if (proof.proof_mode !== "storage_uploaded" && proof.proof_mode !== "live_registered") {
  throw new Error("submission proof must come from live upload; dry-run proofs cannot be registered");
}
const hashToRegister = reportHash(proof);
const storageRoot = requireHash(proof.storage_root_hash, "storage_root_hash");
const storageTxHash = requireHash(proof.storage_tx_hash, "storage_tx_hash");
const contractId = requireContractId(proof.artifact?.contract_id);
const scoreBps = securityScoreBps(proof);
const registryAddress = requireAddress(env("ZERO_G_REGISTRY_ADDRESS"), "ZERO_G_REGISTRY_ADDRESS");

const abi = compileRegistryAbi();
const provider = new ethers.JsonRpcProvider(env("ZERO_G_RPC_URL"));
const wallet = new ethers.Wallet(env("ZERO_G_PRIVATE_KEY"), provider);
const registry = new ethers.Contract(registryAddress, abi, wallet);
const tx = await registry.registerProof(hashToRegister, storageRoot, scoreBps, contractId, storageTxHash);
const receipt = await tx.wait();
const registryTxHash = requireHash(receipt.hash ?? tx.hash, "registry_tx_hash");

const txBase = normalizeBaseUrl(process.env.ZERO_G_EXPLORER_TX_BASE ?? DEFAULT_TX_BASE);
const addressBase = normalizeBaseUrl(process.env.ZERO_G_EXPLORER_ADDRESS_BASE ?? DEFAULT_ADDRESS_BASE);
const updated = {
  ...proof,
  proof_mode: "live_registered",
  registry_address: registryAddress,
  registry_tx_hash: registryTxHash,
  explorer_links: {
    ...(proof.explorer_links ?? {}),
    storage_tx: proof.explorer_links?.storage_tx ?? `${txBase}${storageTxHash}`,
    registry: `${addressBase}${registryAddress}`,
    registration_tx: `${txBase}${registryTxHash}`,
  },
};

delete updated.explorer_links.registry_address;
writeFileSync(inputPath, `${JSON.stringify(updated, null, 2)}\n`);
console.log(JSON.stringify({ proof: inputPath, registry_tx_hash: registryTxHash }, null, 2));
