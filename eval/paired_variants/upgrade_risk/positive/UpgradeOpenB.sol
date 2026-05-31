pragma solidity ^0.8.19;

contract UpgradeOpenB {
    address public implementation;

    function initialize(address impl) external {
        implementation = impl;
    }
}
