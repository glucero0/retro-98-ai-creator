# Security Policy

## Supported versions

This project is a **work in progress**. Security fixes, when issued, are applied to the latest code on the default branch (`main`). Older commits or forks are not separately supported.

## Reporting a vulnerability

If you find a security flaw in this repository’s public code, please report it **privately** — do **not** open a public GitHub issue or discussion for it.

**Preferred:** use GitHub’s private vulnerability reporting for this repo:

https://github.com/glucero0/retro-98-ai-creator/security/advisories/new

If private reporting is unavailable, contact the repository owner ([@glucero0](https://github.com/glucero0)) through a private GitHub channel (for example a maintainer-only email or direct message you already use with them). Do not post exploit details, secrets, or proof-of-concept payloads in public.

Please include:

- A short description of the issue and its impact
- Steps to reproduce (or a minimal proof of concept)
- Affected commit, branch, or release if known
- Any suggested fix, if you have one

## What to expect

- Acknowledgement when the report is received (as capacity allows)
- An initial assessment of severity and whether a fix is planned
- Coordination on disclosure timing when a fix is ready

There is no guaranteed SLA. This software is provided as-is; see the project license and README disclaimer.

## Scope notes

Reports that are especially helpful include issues involving:

- Handling of API keys or other secrets in config or logs
- Local file paths used for `archives.json`, `media/`, or imports/exports
- The local HTTP bridge used by the desktop UI (for example media replace/save endpoints)
- Dependency vulnerabilities in published requirements with a clear exploit path in this app

Out of scope for private security reports (use normal issues instead): feature requests, general bugs without security impact, and third-party service outages (Gemini, OpenRouter, Hugging Face, etc.).
