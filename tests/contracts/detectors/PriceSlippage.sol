pragma solidity ^0.8.19;

contract PriceSlippage {
    function swap(uint256 amountIn, uint256 poolBalance) external pure returns (uint256) {
        return amountIn * 1 ether / poolBalance;
    }
}
