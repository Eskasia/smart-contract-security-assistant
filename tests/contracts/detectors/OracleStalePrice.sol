pragma solidity ^0.8.19;

contract OracleStalePrice {
    int256 public price;
    uint256 public updatedAt;

    function setOraclePrice(int256 newPrice, uint256 timestamp) external {
        price = newPrice;
        updatedAt = timestamp;
    }
}
