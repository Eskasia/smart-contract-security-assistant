pragma solidity ^0.8.19;

contract UpgradeInitializer {
    address public owner;

    function initialize(address newOwner) external {
        owner = newOwner;
    }
}
