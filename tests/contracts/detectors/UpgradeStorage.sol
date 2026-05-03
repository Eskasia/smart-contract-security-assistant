pragma solidity ^0.8.19;

contract UpgradeStorage {
    address public implementation;

    function upgradeTo(address newImplementation) external {
        implementation = newImplementation;
    }
}
