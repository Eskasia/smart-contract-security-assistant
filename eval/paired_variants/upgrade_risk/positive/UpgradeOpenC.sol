pragma solidity ^0.8.19;

contract UpgradeOpenC {
    address public implementation;

    function setImplementation(address impl) public {
        implementation = impl;
    }
}
