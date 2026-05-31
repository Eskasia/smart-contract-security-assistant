pragma solidity ^0.8.19;

contract VaultReentrantB {
    mapping(address => uint256) public balances;

    function claim() external {
        uint256 amount = balances[msg.sender];
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok);
        balances[msg.sender] = 0;
    }
}
