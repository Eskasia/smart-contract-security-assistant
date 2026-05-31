pragma solidity ^0.8.19;

contract UpgradeGuardedC {
    address public owner;
    address public implementation;

    function setImplementation(address impl) public {
        require(msg.sender == owner);
        implementation = impl;
    }
}
