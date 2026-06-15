# Distribution

This folder contains the manifest schema and sample manifest files
that describe firmware releases for the OTA update system.

---

## Files

### manifest_schema.json

JSON Schema defining the structure of every manifest.json file.
Defines required fields, types, patterns, and examples for:

- version
- filename
- sha256
- signature_filename
- released_at
- minimum_version
- description

### manifest.json

A sample manifest generated from dummy_firmware_v1.0.0.bin using
`firmware/generate_manifest.py`. This is what the edge agent reads
to check for updates and verify integrity.

---

## Manifest Lifecycle

1. Developer pushes a release tag (e.g. v1.2.0)
2. CI/CD pipeline (Week 2) signs firmware and computes SHA-256
3. generate_manifest.py creates manifest.json with all fields
4. Pipeline uploads firmware.bin, firmware.sig, manifest.json to S3
5. Edge agent downloads manifest.json to check for updates
6. Edge agent downloads firmware.bin and firmware.sig if update available
7. Edge agent verifies hash and signature against manifest values

---

## S3 Bucket Structure (Week 2)

s3://your-bucket-name/
└── releases/
└── v1.0.0/
├── dummy_firmware_v1.0.0.bin
├── dummy_firmware_v1.0.0.sig
└── manifest.json
└── v1.1.0/
├── dummy_firmware_v1.1.0.bin
├── dummy_firmware_v1.1.0.sig
└── manifest.json

Each release gets its own versioned folder. The edge agent always
checks the latest version's manifest.json to determine if an update
is needed.
