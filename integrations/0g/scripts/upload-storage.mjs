import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";

const DRY_RUN_STORAGE_TX_HASH = "dry-run-only";
const PENDING_REGISTRY_ADDRESS = "pending-live-registry";
const PENDING_REGISTRY_TX_HASH = "pending-live-registration";
const DEFAULT_CHAIN_TX_BASE = "https://chainscan.0g.ai/tx/";
const DEFAULT_EXPECTED_CHAIN_ID = 16661n;

function env(name, fallback = undefined) {
  const value = process.env[name] ?? fallback;
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function hasArg(name) {
  return process.argv.includes(name);
}

function normalizeBaseUrl(value) {
  return value.endsWith("/") ? value : `${value}/`;
}

function expectedChainId() {
  const raw = process.env.ZERO_G_EXPECTED_CHAIN_ID;
  if (raw === undefined || raw === "") {
    return DEFAULT_EXPECTED_CHAIN_ID;
  }
  try {
    const parsed = BigInt(raw);
    if (parsed <= 0n) {
      throw new Error();
    }
    return parsed;
  } catch {
    throw new Error("ZERO_G_EXPECTED_CHAIN_ID must be a positive integer");
  }
}

async function requireExpectedChain(provider) {
  const expected = expectedChainId();
  const network = await provider.getNetwork();
  if (network.chainId !== expected) {
    throw new Error(`ZERO_G_RPC_URL chain id ${network.chainId} does not match expected ${expected}`);
  }
  return network.chainId;
}

function requireFunction(value, label) {
  if (typeof value !== "function") {
    throw new Error(`0G Storage SDK mismatch: expected ${label} to be a function`);
  }
}

function requireHex(value, label, bytes = 32) {
  const pattern = new RegExp(`^0x[0-9a-fA-F]{${bytes * 2}}$`);
  if (typeof value !== "string" || !pattern.test(value)) {
    throw new Error(`${label} must be a 0x-prefixed ${bytes}-byte hex string`);
  }
}

function getContractId(proof) {
  return proof?.report?.contract_id ?? proof?.contract_id ?? null;
}

function reportSha256(proof) {
  return proof?.report?.sha256 ?? null;
}

function securityScore(proof) {
  return proof?.report?.security_score ?? null;
}

function normalizedExplorerLinks(proof) {
  const { registry_address: _legacyRegistryAddress, ...links } = proof.zero_g?.explorer_links ?? {};
  return links;
}

async function uploadToZeroG(inputPath) {
  const [{ Indexer, ZgFile }, { ethers }] = await Promise.all([
    import("@0gfoundation/0g-storage-ts-sdk"),
    import("ethers"),
  ]);

  requireFunction(ZgFile?.fromFilePath, "ZgFile.fromFilePath");
  requireFunction(Indexer, "Indexer constructor");

  const evmRpc = env("ZERO_G_RPC_URL", "https://evmrpc.0g.ai");
  const privateKey = env("ZERO_G_PRIVATE_KEY");
  const indexerRpc = env("ZERO_G_STORAGE_INDEXER_RPC");
  const provider = new ethers.JsonRpcProvider(evmRpc);
  const chainId = await requireExpectedChain(provider);
  const signer = new ethers.Wallet(privateKey, provider);
  const indexer = new Indexer(indexerRpc);
  const file = await ZgFile.fromFilePath(inputPath);

  try {
    requireFunction(file?.merkleTree, "ZgFile instance merkleTree");
    requireFunction(file?.close, "ZgFile instance close");
    requireFunction(indexer?.upload, "Indexer instance upload");

    const merkleResult = await file.merkleTree();
    if (!Array.isArray(merkleResult) || merkleResult.length < 2) {
      throw new Error("0G Storage SDK mismatch: merkleTree must return [tree, error]");
    }
    const [tree, treeError] = merkleResult;
    if (treeError !== null && treeError !== undefined) {
      throw new Error(`0G merkle tree failed: ${treeError}`);
    }
    requireFunction(tree?.rootHash, "merkle tree rootHash");

    const uploadResult = await indexer.upload(file, evmRpc, signer);
    if (!Array.isArray(uploadResult) || uploadResult.length < 2) {
      throw new Error("0G Storage SDK mismatch: upload must return [txHash, error]");
    }
    const [storageTxHash, uploadError] = uploadResult;
    if (uploadError !== null && uploadError !== undefined) {
      throw new Error(`0G upload failed: ${uploadError}`);
    }

    const storageRootHash = tree.rootHash();
    requireHex(storageRootHash, "storage_root_hash");
    requireHex(storageTxHash, "storage_tx_hash");
    return { storageRootHash, storageTxHash, chainId };
  } finally {
    if (typeof file?.close === "function") {
      await file.close();
    }
  }
}

const dryRun = hasArg("--dry-run");
const inputPath = process.argv.find((value, index) => index > 1 && !value.startsWith("--"));

if (!inputPath || !existsSync(inputPath)) {
  throw new Error("Usage: node scripts/upload-storage.mjs <audit-proof.json> [--dry-run]");
}

const proof = JSON.parse(readFileSync(inputPath, "utf-8"));
const txBase = normalizeBaseUrl(
  process.env.ZERO_G_CHAIN_EXPLORER_TX_BASE ?? DEFAULT_CHAIN_TX_BASE,
);
let storageRootHash;
let storageTxHash;
let registryAddress;
let registryTxHash;
let proofMode;
let explorerLinks;
let chainId;

if (dryRun) {
  storageRootHash = `0x${sha256(inputPath)}`;
  storageTxHash = DRY_RUN_STORAGE_TX_HASH;
  registryAddress = PENDING_REGISTRY_ADDRESS;
  registryTxHash = PENDING_REGISTRY_TX_HASH;
  proofMode = "dry_run";
  explorerLinks = {};
} else {
  ({ storageRootHash, storageTxHash, chainId } = await uploadToZeroG(inputPath));
  registryAddress = process.env.ZERO_G_REGISTRY_ADDRESS ?? proof.zero_g?.registry_address ?? PENDING_REGISTRY_ADDRESS;
  registryTxHash = proof.zero_g?.registry_tx_hash ?? PENDING_REGISTRY_TX_HASH;
  proofMode = "storage_uploaded";
  explorerLinks = {
    ...normalizedExplorerLinks(proof),
    storage_tx: `${txBase}${storageTxHash}`,
  };
}

const artifactSha256 = sha256(inputPath);
const output = {
  ...proof.zero_g,
  storage_root_hash: storageRootHash,
  storage_tx_hash: storageTxHash,
  registry_address: registryAddress,
  registry_tx_hash: registryTxHash,
  proof_mode: proofMode,
  chain_id: chainId === undefined ? null : Number(chainId),
  explorer_links: explorerLinks,
  artifact: {
    source_file: inputPath,
    file_name: basename(inputPath),
    sha256: artifactSha256,
    report_sha256: reportSha256(proof),
    security_score: securityScore(proof),
    schema_version: proof.schema_version,
    contract_id: getContractId(proof),
  },
};

const outputPath = join(dirname(inputPath), "submission-proof.json");
writeFileSync(outputPath, `${JSON.stringify(output, null, 2)}\n`);
console.log(JSON.stringify({ output: outputPath, storage_root_hash: storageRootHash }, null, 2));
