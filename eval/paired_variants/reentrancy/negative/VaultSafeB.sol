pragma solidity ^0.8.19;

contract VaultSafeB {
    mapping(address => uint256) public balances;

    modifier nonReentrant() {
        _;
    }

    function claim() external nonReentrant {
        uint256 amount = balances[msg.sender];
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok);
        balances[msg.sender] = 0;
    }
}
