pragma solidity ^0.8.19;

contract DelegatecallOpenC {
    function forward(address plugin, bytes calldata data) public {
        plugin.delegatecall(data);
    }
}
