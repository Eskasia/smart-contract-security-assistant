pragma solidity ^0.8.19;

contract UncheckedCallB {
    function ping(address target, bytes calldata data) external {
        target.delegatecall(data);
    }
}
