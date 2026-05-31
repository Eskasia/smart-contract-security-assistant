pragma solidity ^0.8.19;

contract UpgradeOpenA {
    address public implementation;

    function upgradeTo(address nextImplementation) external {
        implementation = nextImplementation;
    }
}
