// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IERC20TransferFixture {
    function transfer(address to, uint256 amount) external returns (bool);
}

contract UncheckedTransferFixture {
    function fixture(IERC20TransferFixture token, address to, uint256 amount) external {
        token.transfer(to, amount);
    }
}
