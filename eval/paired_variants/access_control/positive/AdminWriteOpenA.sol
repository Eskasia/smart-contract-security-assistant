pragma solidity ^0.8.19;

contract AdminWriteOpenA {
    address public owner;

    function setOwner(address nextOwner) external {
        owner = nextOwner;
    }
}
