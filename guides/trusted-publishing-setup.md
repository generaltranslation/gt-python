# Trusted Publishing Setup (PyPI OIDC)

This is a one-time setup for each package. It allows GitHub Actions to publish to PyPI without API tokens.

## Prerequisites

- A PyPI account with owner/maintainer access
- The GitHub repository must have a `release` environment configured

## GitHub Environment Setup

1. Go to the repository **Settings > Environments**
2. Click **New environment**
3. Name it `release`
4. Optionally add protection rules (e.g., required reviewers)

## Register a Trusted Publisher on PyPI

For each package, register it as a pending publisher on [pypi.org](https://pypi.org):

1. Go to https://pypi.org/manage/account/publishing/
2. Under **"Add a new pending publisher"**, fill in:
   - **PyPI project name**: the package name (e.g., `generaltranslation`)
   - **Owner**: `generaltranslation`
   - **Repository name**: `gt-python`
   - **Workflow name**: `release.yml`
   - **Environment name**: `release`
3. Click **Add**

## Packages to register

Repeat the above for each package:

| PyPI project name |
|---|
| `generaltranslation` |
| `generaltranslation-icu-messageformat-parser` |
| `generaltranslation-intl-messageformat` |
| `generaltranslation-supported-locales` |
| `gt-i18n` |
| `gt-flask` |
| `gt-fastapi` |

## Verification

After setup, the next release will use OIDC (no tokens needed). You can verify by checking the publish job logs in GitHub Actions for "Trusted publisher authentication" messages.
