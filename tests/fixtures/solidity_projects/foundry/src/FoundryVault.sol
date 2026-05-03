pragma solidity ^0.8.19;

import "@local/BaseVault.sol";

contract FoundryVault is BaseVault {
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        (bool success,) = payable(msg.sender).call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
}
