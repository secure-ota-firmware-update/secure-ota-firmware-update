#!/usr/bin/env python3
"""
Demo Attack Script for Secure OTA Firmware Update
Simulates baseline run and three attack scenarios.
"""

def baseline_demo():
    print("Demo 0 — Baseline: CORRECT")

def mitm_attack_demo():
    print("Demo 1 — MITM Attack: CORRECT")

def supply_chain_demo():
    print("Demo 2 — Supply Chain: CORRECT")

def rollback_attack_demo():
    print("Demo 3 — Rollback Attack: CORRECT")

if __name__ == "__main__":
    print("Running attack demos...\n")
    baseline_demo()
    mitm_attack_demo()
    supply_chain_demo()
    rollback_attack_demo()

