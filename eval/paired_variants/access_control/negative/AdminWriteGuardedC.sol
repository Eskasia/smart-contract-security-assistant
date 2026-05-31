pragma solidity ^0.8.19;

contract AdminWriteGuardedC {
    address public owner;
    uint256 public fee;

    function setFee(uint256 nextFee) external {
        require(msg.sender == owner);
        fee = nextFee;
    }
}
