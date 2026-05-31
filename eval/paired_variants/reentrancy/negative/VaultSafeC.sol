pragma solidity ^0.8.19;

contract VaultSafeC {
    mapping(address => uint256) public balances;

    function refund() public {
        uint256 amount = balances[msg.sender];
        balances[msg.sender] = 0;
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
    }
}
