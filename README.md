# Secure OTA Firmware Update & Code Signing Infrastructure

A secure Over-The-Air (OTA) firmware update system for IoT devices.
Firmware is cryptographically signed in a CI/CD pipeline and verified
on the edge device before installation.

## Problem Statement
IoT devices in logistics fleets need remote firmware updates. Without
security, an attacker can intercept the update and push malicious
firmware to the entire fleet. This system prevents that by cryptographically
signing every firmware release and verifying the signature on the device
before any installation happens.

## Tech Stack
- Python 3.11
- ECDSA P-256 — digital signatures
- SHA-256 — integrity hashing
- GitHub Actions — automated CI/CD signing pipeline
- AWS S3 — secure firmware distribution

## Project Structure
- `pki/` — key generation scripts and public key
- `firmware/` — dummy binary, signing script, manifest generator
- `edge_agent/` — simulated IoT device verification agent
- `distribution/` — S3 manifest schema
- `tests/` — tamper simulation and end-to-end tests
- `docs/` — threat model and cryptographic decisions

## Setup
pip install -r requirements.txt

## Team
Infotact Internship — Cybersecurity Project 1
Secure OTA Firmware Update & Code Signing Infrastructure