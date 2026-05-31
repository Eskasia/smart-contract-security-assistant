pragma solidity ^0.8.19;

contract AdminWriteOpenC {
    uint256 public fee;

    function setFee(uint256 nextFee) external {
        fee = nextFee;
    }
}
