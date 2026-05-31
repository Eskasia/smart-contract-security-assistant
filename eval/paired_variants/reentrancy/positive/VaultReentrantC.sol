pragma solidity ^0.8.19;

contract VaultReentrantC {
    mapping(address => uint256) public balances;

    function refund() public {
        uint256 amount = balances[msg.sender];
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
}
