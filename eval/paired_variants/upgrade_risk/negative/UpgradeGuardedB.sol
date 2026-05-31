pragma solidity ^0.8.19;

contract UpgradeGuardedB {
    address public implementation;

    modifier initializer() {
        _;
    }

    function initialize(address impl) external initializer {
        implementation = impl;
    }
}
