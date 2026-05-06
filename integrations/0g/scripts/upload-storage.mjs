import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";

const ZERO_HASH = `0x${"00".repeat(32)}`;
const DEFAULT_TX_BASE = "https://www.0gscan.com/tx/";
const DEFAULT_ADDRESS_BASE = "https://www.0gscan.com/address/";

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
    return { storageRootHash, storageTxHash };
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
const txBase = normalizeBaseUrl(process.env.ZERO_G_EXPLORER_TX_BASE ?? DEFAULT_TX_BASE);
const addressBase = normalizeBaseUrl(process.env.ZERO_G_EXPLORER_ADDRESS_BASE ?? DEFAULT_ADDRESS_BASE);
const registryAddress = process.env.ZERO_G_REGISTRY_ADDRESS ?? proof.zero_g?.registry_address ?? ZERO_HASH.slice(0, 42);
const registryTxHash = proof.zero_g?.registry_tx_hash ?? ZERO_HASH;
let storageRootHash;
let storageTxHash;

if (dryRun) {
  storageRootHash = `0x${sha256(inputPath)}`;
  storageTxHash = ZERO_HASH;
} else {
  ({ storageRootHash, storageTxHash } = await uploadToZeroG(inputPath));
}

const artifactSha256 = sha256(inputPath);
const output = {
  ...proof.zero_g,
  storage_root_hash: storageRootHash,
  storage_tx_hash: storageTxHash,
  registry_address: registryAddress,
  registry_tx_hash: registryTxHash,
  explorer_links: {
    ...(proof.zero_g?.explorer_links ?? {}),
    storage_tx: `${txBase}${storageTxHash}`,
    registration_tx: `${txBase}${registryTxHash}`,
    registry: `${addressBase}${registryAddress}`,
  },
  artifact: {
    source_file: inputPath,
    file_name: basename(inputPath),
    sha256: artifactSha256,
    schema_version: proof.schema_version,
    contract_id: getContractId(proof),
  },
};

const outputPath = join(dirname(inputPath), "submission-proof.json");
writeFileSync(outputPath, `${JSON.stringify(output, null, 2)}\n`);
console.log(JSON.stringify({ output: outputPath, storage_root_hash: storageRootHash }, null, 2));
