pragma solidity ^0.8.19;

contract CheckedCallB {
    function ping(address target, bytes calldata data) external {
        (bool success, ) = target.delegatecall(data);
        if (!success) revert();
    }
}
