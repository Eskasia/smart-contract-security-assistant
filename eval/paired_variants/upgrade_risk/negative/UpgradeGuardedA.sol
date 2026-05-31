pragma solidity ^0.8.19;

contract UpgradeGuardedA {
    address public owner;
    address public implementation;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function upgradeTo(address nextImplementation) external onlyOwner {
        implementation = nextImplementation;
    }
}
