pragma solidity ^0.8.19;

contract SharedVault {
    mapping(address => uint256) internal balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
}
