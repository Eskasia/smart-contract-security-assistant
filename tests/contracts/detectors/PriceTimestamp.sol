pragma solidity ^0.8.19;

contract PriceTimestamp {
    function quote(uint256 base) external view returns (uint256) {
        return base + (block.timestamp % 10);
    }
}
