pragma solidity ^0.8.19;

contract UncheckedCallC {
    function viewPing(address target, bytes calldata data) external view {
        target.staticcall(data);
    }
}
