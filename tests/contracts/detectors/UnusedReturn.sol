// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract UnusedReturnFixture {
    function target() external pure returns (bool) {
        return true;
    }

    function fixture(UnusedReturnFixture targetContract) external {
        targetContract.target();
    }
}
