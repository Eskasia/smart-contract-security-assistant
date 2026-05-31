pragma solidity ^0.8.19;

contract DelegatecallGuardedB {
    address public trustedTarget;

    function run(bytes calldata data) external {
        trustedTarget.delegatecall(data);
    }
}
