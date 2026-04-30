// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ImportBaseVault.sol";

contract ImportEntryVault is ImportBaseVault {
    function version() external pure returns (uint256) {
        return 1;
    }
}
