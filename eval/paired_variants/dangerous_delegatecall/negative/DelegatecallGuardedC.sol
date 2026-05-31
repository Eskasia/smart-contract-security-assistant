pragma solidity ^0.8.19;

contract DelegatecallGuardedC {
    mapping(address => bool) public allowlisted;

    function forward(address plugin, bytes calldata data) public {
        require(allowlisted[plugin]);
        plugin.delegatecall(data);
    }
}
