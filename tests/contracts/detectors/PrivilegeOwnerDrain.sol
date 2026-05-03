pragma solidity ^0.8.19;

contract PrivilegeOwnerDrain {
    address public owner;

    function sweep(address payable to) external {
        to.transfer(address(this).balance);
    }
}
