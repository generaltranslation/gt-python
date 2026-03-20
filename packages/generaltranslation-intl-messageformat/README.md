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

# generaltranslation-intl-messageformat

> ⚠️ **Experimental / Unstable** — This package is under active development and may be subject to breaking changes.

ICU MessageFormat formatter with locale-aware plural and select rules. Python equivalent of [`intl-messageformat`](https://www.npmjs.com/package/intl-messageformat).

## Installation

```bash
pip install generaltranslation-intl-messageformat
```

## Quick Start

```python
from generaltranslation_intl_messageformat import IntlMessageFormat

mf = IntlMessageFormat("{count, plural, one {# item} other {# items}}", "en")
mf.format({"count": 1})   # "1 item"
mf.format({"count": 5})   # "5 items"
```
