# Contributing to General Translation (Python)

First off, thanks for taking the time to contribute!

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them.

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation:
>
> - Star the project
> - Post about it
> - Tell your friends/colleagues!

## Table of Contents

- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
- [Development Setup](#development-setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Recommended Editor Extensions](#recommended-editor-extensions)
  - [Common Commands](#common-commands)
- [Styleguides](#styleguides)
  - [Code Style](#code-style)
  - [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)

## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://generaltranslation.com/docs).

Before you ask a question, it is best to search for existing [Issues](https://github.com/generaltranslation/gt-python/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/generaltranslation/gt-python/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (Python, uv, OS, etc.), depending on what seems relevant.

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice
>
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project licence.

### Reporting Bugs

#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Please complete the following steps in advance:

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions. Make sure that you have read the [documentation](https://generaltranslation.com/docs).
- Check if there is not already a bug report existing for your bug or error in the [bug tracker](https://github.com/generaltranslation/gt-python/issues?q=label%3Abug).
- Collect information about the bug:
  - Stack trace (Traceback)
  - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
  - Python version, uv version, package versions
  - Your input and the output
  - Can you reliably reproduce the issue?

#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent by email to <support@generaltranslation.com>.

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/generaltranslation/gt-python/issues/new).
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the _reproduction steps_ that someone else can follow to recreate the issue on their own.
- Provide the information you collected in the previous section.

### Suggesting Enhancements

Enhancement suggestions are tracked as [GitHub issues](https://github.com/generaltranslation/gt-python/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why.
- **Explain why this enhancement would be useful** to most General Translation users.

### Your First Code Contribution

1. Fork the repository
2. Create a feature/fix/refactor/etc. branch (`git checkout -b feature/my-feature`)
3. Follow the [Development Setup](#development-setup) instructions below
4. Make your changes
5. Run tests and linting to make sure everything passes
6. Commit your changes and open a pull request

## Development Setup

### Prerequisites

- **Python 3.10+**

### Installation

Clone the repository and run the setup script:

```bash
git clone https://github.com/generaltranslation/gt-python.git
cd gt-python
./scripts/setup.sh
```

The setup script installs everything you need:

- [uv](https://docs.astral.sh/uv/) — package manager and workspace tool
- All workspace packages (as editable installs in `.venv/`)
- [Rust/Cargo](https://rustup.rs/) — needed to install Sampo
- [Sampo](https://github.com/bruits/sampo) — release automation tool

Changes to source code are immediately reflected — no rebuild needed.

### Recommended Editor Extensions

If you're using VS Code, install the following extensions:

| Extension | ID | Purpose |
| --------- | -- | ------- |
| Python | `ms-python.python` | IntelliSense, debugging, virtualenv support (includes Pylance) |
| Mypy Type Checker | `ms-python.mypy-type-checker` | Inline mypy type errors (matches project config) |
| Ruff | `charliermarsh.ruff` | Linting and formatting (matches project config) |
| Even Better TOML | `tamasfe.even-better-toml` | Syntax highlighting for `pyproject.toml` |

### Common Commands

```bash
make setup          # Install uv, workspace packages, and sampo
make lint           # Run ruff linter
make format         # Auto-format with ruff
make format-check   # Check formatting without changes
make typecheck      # Run mypy type checking
make test           # Run all tests
make check          # Run all checks (lint + format + typecheck + test)
make build          # Build all packages to dist/
make changeset      # Add a changeset for your changes (sampo add)
make clean          # Remove build artifacts and caches
```

To run tests for a specific package:

```bash
uv run pytest packages/generaltranslation/
```

### Releasing

This project uses [Sampo](https://github.com/bruits/sampo) for automated releases. When you make a change that should be released, add a changeset:

```bash
sampo add
```

This prompts you to select affected packages and the bump type (patch/minor/major), then creates a changeset file in `.sampo/changesets/`. Commit this file with your PR.

When your PR merges to `main`, a GitHub Action automatically creates a Release PR that bumps versions and updates changelogs. Merging that Release PR publishes the packages to PyPI.

See `guides/releasing.md` for the full workflow.

## Styleguides

### Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Configuration is in the root `pyproject.toml`.

- Follow PEP 8 naming conventions (`snake_case` for functions and variables, `PascalCase` for classes)
- Use type annotations for all public function signatures
- Keep functions focused and small
- Add docstrings to public functions and classes

### Commit Messages

Please use [Semantic Commit Messages](https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716).
For the scope, you can also mention the package names.
Use clear, descriptive commit messages that explain the "why" behind the change.

These commit conventions are generally most important on commits to main.
All branch commits get squash-merged.

## Join The Project Team

Interested in joining the team? Reach out on [Discord](https://discord.gg/W99K6fchSu) or email us at [hello@generaltranslation.com](mailto:hello@generaltranslation.com).

## Attribution

This guide is based on the [contributing.md](https://contributing.md/generator)!
