pragma solidity ^0.8.19;

contract UncheckedCallA {
    function pay(address target) external {
        target.call("");
    }
}
