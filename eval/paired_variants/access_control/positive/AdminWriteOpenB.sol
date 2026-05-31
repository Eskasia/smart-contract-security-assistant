pragma solidity ^0.8.19;

contract AdminWriteOpenB {
    address public treasury;

    function setTreasury(address nextTreasury) public {
        treasury = nextTreasury;
    }
}
