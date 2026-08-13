# Security Policy

## Supported versions

Security fixes are applied to the latest code on the `main` branch. Older tags may not receive patches.

## Reporting a vulnerability

Please do not disclose suspected vulnerabilities in a public issue, discussion, or pull request.

Use GitHub's **Report a vulnerability** option on this repository's Security tab. Include:

- the affected endpoint, WebSocket message, or component;
- steps to reproduce or a minimal proof of concept;
- the likely impact;
- any suggested mitigation; and
- whether the issue has been disclosed elsewhere.

If private vulnerability reporting is unavailable, contact the repository owner through their GitHub profile before sharing sensitive details.

You should receive an acknowledgment within seven days. Please allow time to investigate and release a fix before public disclosure.

## Deployment responsibility

Whisper Server has not been presented as independently security-audited. Operators are responsible for TLS termination, secret rotation, network isolation, backups, dependency updates, monitoring, and secure client-side key handling.
