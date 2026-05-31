pragma solidity ^0.8.19;

contract CheckedCallA {
    function pay(address target) external {
        (bool success, ) = target.call("");
        require(success);
    }
}
