pragma solidity ^0.8.19;

contract AdminWriteGuardedA {
    address public owner;
    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    function setOwner(address nextOwner) external onlyOwner {
        owner = nextOwner;
    }
}
