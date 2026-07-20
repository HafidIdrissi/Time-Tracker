# Windows Code Signing

The GitHub installer can be downloaded and tested without a digital signature.
For broad public distribution, especially through download portals, H.I.
SOLUTIONS should sign the application executable and installer with a trusted
Authenticode certificate.

## Why signing matters

An unsigned executable may trigger Microsoft Defender SmartScreen warnings.
Signing proves which publisher produced a particular file and detects changes
made after signing. It does not certify that software is bug-free or secure.

The MIT License is a software copyright license; it is unrelated to an
Authenticode signing certificate.

## Certificate options

- **Organization Validation (OV):** identifies the publisher after validation
  by a certificate authority. Reputation is generally built over time.
- **Extended Validation (EV):** uses stronger identity and key-protection
  requirements and is typically more expensive.
- **Microsoft Store signing:** available through a separate MSIX packaging and
  Store submission process.

A self-signed certificate is useful only for controlled internal testing. It is
not trusted automatically on other users' computers and is not suitable for
public download platforms.

## Build-script integration

`build_release.ps1` supports a certificate installed in the Windows certificate
store. Set both variables before building:

```powershell
$env:TIME_TRACKER_SIGNTOOL = "C:\Path\To\signtool.exe"
$env:TIME_TRACKER_CERT_SHA1 = "CERTIFICATE_THUMBPRINT"
.\build_release.ps1 -Version 1.1.0
```

The script signs and verifies both:

- `dist\LocalTimeTracker\LocalTimeTracker.exe`;
- `release\LocalTimeTracker-Setup-1.1.0-x64.exe`.

It uses SHA-256 file digests and a trusted timestamp server, allowing the
signature to remain valid after the certificate expires if it was valid when
timestamped.

## Before public submission

1. purchase a certificate from a certificate authority trusted by Windows;
2. protect the private key and restrict who can sign releases;
3. build from a clean, reviewed commit;
4. verify the Authenticode signature and SHA-256 checksum;
5. scan the exact signed installer submitted to the platform;
6. publish the installer and checksum from the same GitHub release.

Never commit certificates, private keys, passwords, or signing tokens to this
repository.
