<p align="center">
  <a href="https://generaltranslation.com/docs/python">
    <picture>
      <source media="(prefers-color-scheme: light)" srcset="https://generaltranslation.com/brand/gt-logo-light.svg">
      <img alt="General Translation" src="https://generaltranslation.com/brand/gt-logo-dark.svg" width="100" height="100">
    </picture>
  </a>
</p>

<p align="center">
  <a href="https://generaltranslation.com/docs/python"><strong>Documentation</strong></a> · <a href="https://github.com/generaltranslation/gt-python/issues">Report Bug</a>
</p>

# gt-i18n

> ⚠️ **Experimental / Unstable** — This package is under active development and may be subject to breaking changes.

Core Python i18n library for General Translation.

## Installation

```bash
pip install gt-i18n
```

## Quick Start

```python
from gt_i18n import t, init_gt

init_gt(default_locale="en", locales=["en", "es", "fr"])

print(t("Hello, world!"))
```

See the [full documentation](https://generaltranslation.com/docs/python) for guides and API reference.
