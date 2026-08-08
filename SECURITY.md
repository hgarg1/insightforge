# Security Policy

## Supported versions

Security fixes are provided for the latest published release and the current `main` branch.

| Version | Supported |
| --- | --- |
| Latest release | Yes |
| `main` | Yes |
| Older releases | No |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or include secrets, credentials, personal data, or exploit details in an issue.

Report vulnerabilities privately through GitHub's **Report a vulnerability** feature on the repository Security tab. If private vulnerability reporting is unavailable, email [harshit.garg@harshit-garg.com](mailto:harshit.garg@harshit-garg.com) with the subject `InsightForge security report`.

Include the affected version, reproduction steps, expected impact, and any suggested mitigation. You should receive an acknowledgment within seven days. Disclosure timing will be coordinated after a fix is available.

## Scope

In scope:

- Authentication and authorization bypasses.
- Exposure of uploaded workbook data or local secrets.
- Unsafe file handling, path traversal, or code execution.
- Release-pipeline, installer, and update-integrity issues.

Out of scope:

- Vulnerabilities that require unsupported operating systems or modified builds.
- Social engineering, denial-of-service testing, or destructive testing against third-party systems.
- Reports that contain no reproducible security impact.
