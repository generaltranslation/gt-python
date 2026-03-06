# Releasing Packages

This project uses [Sampo](https://github.com/bruits/sampo) for automated releases. Sampo is a Changesets-inspired tool with native Python/PyPI support.

## How it works

### 1. Add a changeset

When you make a change that should be released, run:

```bash
sampo add
```

This prompts you to:
- Select the affected package(s)
- Choose the bump type (patch / minor / major)
- Write a summary of the change

A changeset file is created in `.sampo/changesets/`. Commit this file with your PR.

### 2. Merge to main

When your PR merges to `main`, the release GitHub Action runs automatically. If there are pending changesets, Sampo creates (or updates) a **Release PR** that:
- Bumps package versions in `pyproject.toml`
- Updates `CHANGELOG.md` for each affected package
- Consumes the changeset files

### 3. Merge the Release PR

When the Release PR is merged, the action runs again. This time:
- Sampo creates git tags for each released package
- GitHub releases are created
- The **publish** job builds all packages and publishes them to PyPI using trusted publishing (OIDC)

## First-time setup for a new package

Before a new package can be published, it must be registered as a trusted publisher on PyPI. See [trusted-publishing-setup.md](./trusted-publishing-setup.md).

## Manual release (emergency)

If you need to publish manually:

```bash
# Build a specific package
uv build --package <package-name> --out-dir dist/

# Upload (requires PyPI API token)
uv publish dist/<package-name>-*.tar.gz dist/<package-name>-*.whl
```
