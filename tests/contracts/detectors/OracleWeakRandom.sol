pragma solidity ^0.8.19;

contract OracleWeakRandom {
    function pseudoPrice() external view returns (uint256) {
        return uint256(blockhash(block.number - 1));
    }
}
