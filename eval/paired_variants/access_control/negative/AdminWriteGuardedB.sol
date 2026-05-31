pragma solidity ^0.8.19;

contract AdminWriteGuardedB {
    address public owner;
    address public treasury;

    function setTreasury(address nextTreasury) public {
        require(msg.sender == owner);
        treasury = nextTreasury;
    }
}
