// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract AuditProofRegistry {
    struct AuditProof {
        bytes32 reportHash;
        bytes32 storageRoot;
        uint16 securityScoreBps;
        uint64 createdAt;
        string contractId;
        string storageTxHash;
    }

    address public immutable owner;
    uint256 public proofCount;
    mapping(uint256 => AuditProof) public proofs;

    event AuditProofRegistered(
        uint256 indexed proofId,
        bytes32 indexed reportHash,
        bytes32 indexed storageRoot,
        uint16 securityScoreBps,
        string contractId,
        string storageTxHash
    );

    error NotOwner();

    constructor() {
        owner = msg.sender;
    }

    function registerProof(
        bytes32 reportHash,
        bytes32 storageRoot,
        uint16 securityScoreBps,
        string calldata contractId,
        string calldata storageTxHash
    ) external returns (uint256 proofId) {
        if (msg.sender != owner) {
            revert NotOwner();
        }

        proofId = ++proofCount;
        proofs[proofId] = AuditProof({
            reportHash: reportHash,
            storageRoot: storageRoot,
            securityScoreBps: securityScoreBps,
            createdAt: uint64(block.timestamp),
            contractId: contractId,
            storageTxHash: storageTxHash
        });

        emit AuditProofRegistered(
            proofId,
            reportHash,
            storageRoot,
            securityScoreBps,
            contractId,
            storageTxHash
        );
    }
}
