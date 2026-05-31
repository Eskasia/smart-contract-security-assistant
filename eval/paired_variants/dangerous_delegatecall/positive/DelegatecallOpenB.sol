pragma solidity ^0.8.19;

contract DelegatecallOpenB {
    address public implementation;

    function run(bytes calldata data) external {
        implementation.delegatecall(data);
    }
}
