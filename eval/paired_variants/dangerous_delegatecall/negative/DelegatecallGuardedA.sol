pragma solidity ^0.8.19;

contract DelegatecallGuardedA {
    address public owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function execute(address target, bytes calldata data) external onlyOwner {
        target.delegatecall(data);
    }
}
