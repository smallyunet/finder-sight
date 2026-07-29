# Security Policy

## Supported versions

Security fixes are provided for the latest published Finder Sight release.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature on the repository's **Security** tab when it
is available. Include:

- the affected version and macOS version;
- a minimal reproduction;
- the expected and observed behavior; and
- the potential security or privacy impact.

If private reporting is unavailable, open a GitHub issue requesting a private reporting channel.
Do not include exploit details, private data, credentials, or sensitive file paths in a public issue.

## Security properties

- Image analysis and search run locally using native macOS frameworks.
- Images and derived image features are not uploaded.
- There is no hosted Finder Sight backend, account system, analytics, or telemetry.
- The only application network request is a user-initiated GitHub Releases update check documented
  in [PRIVACY.md](PRIVACY.md).
- The Swift package has no third-party package dependencies.
- Duplicate cleanup uses the recoverable macOS Trash operation.

These properties describe the current implementation. They are not a guarantee that the software
is free of vulnerabilities.

## Automated checks

The repository uses:

- macOS CI tests and native app-bundle builds;
- GitHub CodeQL analysis for Swift;
- OpenSSF Scorecard security-practice analysis; and
- pinned GitHub Action commit references in release and security workflows.

## Verifying release artifacts

Official releases include:

- `FinderSight-macOS.dmg`;
- `FinderSight-macOS.dmg.sha256`; and
- a GitHub artifact attestation tied to the source repository and workflow.

After downloading both files, verify the checksum:

```bash
shasum -a 256 -c FinderSight-macOS.dmg.sha256
```

With the GitHub CLI installed, verify build provenance:

```bash
gh attestation verify FinderSight-macOS.dmg -R smallyunet/finder-sight
```

When the repository has a `VT_API_KEY` Actions secret configured, tagged releases are also
submitted to VirusTotal and the public report is linked from the release notes.

## Apple signing status

Finder Sight is currently ad-hoc signed. It is not signed with an Apple Developer ID and is not
notarized by Apple. GitHub attestations, checksums, CodeQL, OpenSSF Scorecard, and VirusTotal reports
provide independent evidence, but none is a substitute for Apple Developer ID signing and
notarization.
