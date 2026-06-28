# Anti-Rollback Protection

This document explains the anti-rollback version enforcement mechanism
implemented in `edge_agent/agent.py` and `edge_agent/version_store.json`.

---

## The Problem — Rollback Attacks

ECDSA signature verification alone is not sufficient protection.
Consider this scenario:

1. Firmware v1.0.0 is released with a known vulnerability (e.g. a
   remote code execution bug in the GPS reporting module)
2. The vulnerability is discovered and patched in v1.1.0
3. v1.1.0 is deployed to all devices
4. v1.0.0 was legitimately signed with the developer's private key
5. An attacker re-serves v1.0.0 to devices currently running v1.1.0

Without anti-rollback protection, the device would:
- Download v1.0.0
- Verify the hash — PASS (binary was not modified)
- Verify the signature — PASS (was legitimately signed)
- Install v1.0.0 — re-exposing the device to the patched vulnerability

This is Threat 3 from `docs/THREAT_MODEL.md`.

---

## The Solution — Minimum Version Enforcement

The device maintains a `minimum_version` field in
`edge_agent/version_store.json`. Before installing any update,
the agent checks:

ncoming_version >= minimum_version

If this check fails, the firmware is rejected even if both the
SHA-256 hash and ECDSA signature are completely valid.

---

## Version Store Structure

```json
{
  "current_version": "1.0.0",
  "minimum_version": "1.0.0",
  "last_updated": "2026-06-21T10:00:00Z",
  "install_history": [
    {
      "version": "1.0.0",
      "installed_at": "2026-06-21T10:00:00Z",
      "previous_version": "0.0.0",
      "minimum_version_raised_to": "1.0.0",
      "status": "success"
    }
  ]
}
```

### Fields

**current_version**
The firmware version currently installed and running on the device.
Updated after every successful install.

**minimum_version**
The lowest version the device will accept for installation.
Starts at the initial deployment version.
Automatically raised to match current_version after each successful
install — so the minimum only ever moves forward, never backward.

**last_updated**
UTC timestamp of the last version store write operation.

**install_history**
Chronological list of all firmware installs on this device.
Used as an audit trail. Includes what version was installed,
when, what the previous version was, and what the minimum was
raised to.

---

## How minimum_version Moves Forward

After a successful install of v1.2.0:
Before install:

current_version: "1.1.0"

minimum_version: "1.1.0"
After install:

current_version: "1.2.0"

minimum_version: "1.2.0"

The minimum is raised to 1.2.0. This means:
- v1.2.0 can be re-installed (equal is allowed)
- v1.2.1+ can be installed (newer is allowed)
- v1.1.0 is permanently blocked (even though legitimately signed)
- v1.0.0 is permanently blocked (even though legitimately signed)

---

## Version Comparison — Why Not String Comparison

Version comparison uses integer tuple comparison, not string comparison.

**String comparison gives wrong results:**
```python
"1.10.0" < "1.9.0"  # True — WRONG (lexicographic order)
"1.2.0" > "1.10.0"  # True — WRONG
```

**Integer comparison gives correct results:**
```python
(1, 10, 0) > (1, 9, 0)  # True — CORRECT
(1, 2, 0) < (1, 10, 0)  # True — CORRECT
```

The `anti_rollback_check()` function splits version strings on "."
and converts each part to an integer before comparing. See
`edge_agent/agent.py` for the implementation.

---

## Rejection Report on Rollback Attempt

When a rollback is detected, the agent:

1. Logs 5 CRITICAL lines identifying the security event
2. Writes a JSON rejection report to `edge_agent/rejections/` with:
   - `reason: "ROLLBACK_ATTEMPT"`
   - Incoming version and minimum version recorded
   - Timestamp and UUID for correlation
3. Deletes the downloaded firmware and signature files
4. Aborts without installing anything

Sample rejection report:
```json
{
  "report_id": "abc123-...",
  "timestamp": "2026-06-21T10:00:00Z",
  "severity": "CRITICAL",
  "reason": "ROLLBACK_ATTEMPT",
  "firmware_version": "0.9.0",
  "details": "Incoming version v0.9.0 is below minimum v1.0.0. Rollback attack suspected.",
  "action_taken": "Firmware payload dropped. Installation refused."
}
```

---

## Test Coverage

| Test | Scenario | Result |
|------|----------|--------|
| test_anti_rollback_accepts_newer_version | v1.2.0 >= v1.0.0 | ACCEPTED |
| test_anti_rollback_accepts_equal_version | v1.0.0 == v1.0.0 | ACCEPTED |
| test_anti_rollback_rejects_older_major | v0.9.0 < v1.0.0 | REJECTED |
| test_anti_rollback_rejects_older_patch | v1.0.0 < v1.0.1 | REJECTED |
| test_anti_rollback_integer_comparison_correctness | v1.10.0 > v1.9.0 | ACCEPTED |

See `tests/test_local_pipeline.py` for automated test implementation.

---

## Relationship to the Three Security Layers

The complete firmware verification stack after Week 3:
Layer 1 — SHA-256 Hash Check

Detects any modification to the firmware binary in transit.

Even a single bit change is caught.
Layer 2 — ECDSA Signature Verification

Proves the firmware was signed by the legitimate private key holder.

Cannot be forged without the private key.
Layer 3 — Anti-rollback Version Check

Prevents installation of older firmware even if legitimately signed.

Minimum version only moves forward, never backward.

An attacker must defeat ALL THREE layers to successfully install
malicious firmware. This is computationally and operationally
infeasible with this architecture.

---

## Production Considerations

In a production system:

**Hardware-enforced anti-rollback:**
Modern SoCs (e.g. nRF52, STM32) have OTP (One-Time Programmable)
registers that store the minimum firmware version in hardware.
Even if the OS is compromised, the hardware bootloader enforces
the minimum version and refuses to boot older firmware.

**TUF (The Update Framework):**
TUF's snapshot and timestamp metadata include version tracking
that provides server-side anti-rollback guarantees in addition
to device-side enforcement.

**See also:**
`docs/ARCHITECTURE_DECISIONS.md` for overall system design decisions.
`docs/THREAT_MODEL.md` for Threat 3 (Rollback Attack) full analysis.
