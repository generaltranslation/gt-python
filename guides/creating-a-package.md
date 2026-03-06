# Creating a New Package

This guide covers adding a new Python package to the gt-python monorepo.

## 1. Create the directory structure

```
packages/my-package/
  src/
    my_package/
      __init__.py
  pyproject.toml
  README.md
  LICENSE.md
```

## 2. Set up `pyproject.toml`

Use the `uv_build` backend and follow the existing conventions:

```toml
[project]
name = "my-package"
version = "0.0.0"
description = "Description of your package"
readme = "README.md"
authors = [
    { name = "Your Name", email = "you@generaltranslation.com" }
]
requires-python = ">=3.10"
license = "FSL-1.1-ALv2"
license-files = ["LICENSE.md"]
dependencies = []

[build-system]
requires = ["uv_build>=0.10.8,<0.11.0"]
build-backend = "uv_build"
```

## 3. Add workspace source references

If your package depends on other workspace packages, add `[tool.uv.sources]` entries:

```toml
[tool.uv.sources]
generaltranslation = { workspace = true }
```

## 4. Register the package in the workspace

The root `pyproject.toml` uses `packages/*/` as the workspace members glob, so new packages under `packages/` are automatically discovered.

Run `uv sync --all-packages` to verify the new package is picked up.

## 5. Register as a trusted publisher on PyPI

Before the first release, you must register the package as a pending publisher on PyPI. See [trusted-publishing-setup.md](./trusted-publishing-setup.md) for step-by-step instructions.

## 6. Build and test

```bash
# Build the package
uv build --package my-package

# Run tests
uv run pytest packages/my-package/
```
