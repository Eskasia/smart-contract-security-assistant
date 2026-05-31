pragma solidity ^0.8.19;

contract DelegatecallOpenA {
    function execute(address target, bytes calldata data) external {
        target.delegatecall(data);
    }
}
