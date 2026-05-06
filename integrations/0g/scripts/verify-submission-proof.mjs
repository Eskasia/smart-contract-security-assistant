import { existsSync, readFileSync } from "node:fs";

const TX_BASE = process.env.ZERO_G_EXPLORER_TX_BASE ?? "https://www.0gscan.com/tx/";
const ADDRESS_BASE = process.env.ZERO_G_EXPLORER_ADDRESS_BASE ?? "https://www.0gscan.com/address/";
const HASH_PATTERN = /^0x[0-9a-fA-F]{64}$/;
const ADDRESS_PATTERN = /^0x[0-9a-fA-F]{40}$/;
const DRY_RUN_STORAGE_TX_HASH = "dry-run-only";
const PENDING_REGISTRY_ADDRESS = "pending-live-registry";
const PENDING_REGISTRY_TX_HASH = "pending-live-registration";

function normalizeBaseUrl(value) {
  return value.endsWith("/") ? value : `${value}/`;
}

function requireField(proof, key, pattern = null) {
  const value = proof[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Missing proof field: ${key}`);
  }
  if (pattern !== null && !pattern.test(value)) {
    throw new Error(`Invalid proof field: ${key}`);
  }
}

function requireArtifactField(proof, key) {
  const value = proof.artifact?.[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Missing artifact field: ${key}`);
  }
}

function requireLink(proof, key, expected) {
  const value = proof.explorer_links?.[key];
  if (value !== expected) {
    throw new Error(`Invalid explorer link: ${key}`);
  }
}

function requireLiteral(proof, key, expected) {
  if (proof[key] !== expected) {
    throw new Error(`Invalid dry-run proof field: ${key}`);
  }
}

function requireNoExplorerLinks(proof) {
  const links = proof.explorer_links ?? {};
  const keys = Object.keys(links);
  if (keys.length > 0) {
    throw new Error(`Dry-run proof must not include explorer links: ${keys.join(", ")}`);
  }
}

function rejectLegacyLink(proof, key) {
  if (Object.hasOwn(proof.explorer_links ?? {}, key)) {
    throw new Error(`Legacy explorer link is not supported: ${key}`);
  }
}

const inputPath = process.argv[2];
if (!inputPath || !existsSync(inputPath)) {
  throw new Error("Usage: node scripts/verify-submission-proof.mjs <submission-proof.json>");
}

const proof = JSON.parse(readFileSync(inputPath, "utf-8"));
requireField(proof, "storage_root_hash", HASH_PATTERN);
requireArtifactField(proof, "source_file");
requireArtifactField(proof, "file_name");
requireArtifactField(proof, "sha256");
requireArtifactField(proof, "schema_version");
requireArtifactField(proof, "contract_id");

rejectLegacyLink(proof, "registry_address");

if (proof.proof_mode === "dry_run") {
  requireLiteral(proof, "storage_tx_hash", DRY_RUN_STORAGE_TX_HASH);
  requireLiteral(proof, "registry_address", PENDING_REGISTRY_ADDRESS);
  requireLiteral(proof, "registry_tx_hash", PENDING_REGISTRY_TX_HASH);
  requireNoExplorerLinks(proof);
} else if (proof.proof_mode === "live_registered") {
  requireField(proof, "storage_tx_hash", HASH_PATTERN);
  requireField(proof, "registry_address", ADDRESS_PATTERN);
  requireField(proof, "registry_tx_hash", HASH_PATTERN);
  const txBase = normalizeBaseUrl(TX_BASE);
  const addressBase = normalizeBaseUrl(ADDRESS_BASE);
  requireLink(proof, "storage_tx", `${txBase}${proof.storage_tx_hash}`);
  requireLink(proof, "registration_tx", `${txBase}${proof.registry_tx_hash}`);
  requireLink(proof, "registry", `${addressBase}${proof.registry_address}`);
} else if (proof.proof_mode === "storage_uploaded") {
  throw new Error("Proof is uploaded but not registered; run npm run register before final verification");
} else {
  throw new Error("proof_mode must be dry_run or live_registered");
}

console.log(JSON.stringify({ ok: true, proof: inputPath }, null, 2));
