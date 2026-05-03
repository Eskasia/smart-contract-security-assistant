pragma solidity ^0.8.19;

contract PrivilegeTxOrigin {
    address public owner;

    function setOwner(address newOwner) external {
        require(tx.origin == owner);
        owner = newOwner;
    }
}
