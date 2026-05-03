pragma solidity ^0.8.19;

import "./level1/NestedMiddle.sol";

contract NestedVault is NestedMiddle {
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        (bool success,) = payable(msg.sender).call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
}
