pragma solidity ^0.8.19;

contract CheckedCallC {
    function viewPing(address target, bytes calldata data) external view {
        (bool success, ) = target.staticcall(data);
        assert(success);
    }
}
