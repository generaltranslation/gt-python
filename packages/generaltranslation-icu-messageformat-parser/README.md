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

# generaltranslation-icu-messageformat-parser

> ⚠️ **Experimental / Unstable** — This package is under active development and may be subject to breaking changes.

A pure-Python ICU MessageFormat parser. Python equivalent of [`@formatjs/icu-messageformat-parser`](https://www.npmjs.com/package/@formatjs/icu-messageformat-parser).

## Installation

```bash
pip install generaltranslation-icu-messageformat-parser
```

## Quick Start

```python
from generaltranslation_icu_messageformat_parser import Parser, print_ast

parser = Parser()
ast = parser.parse("{count, plural, one {# item} other {# items}}")
print(print_ast(ast))  # "{count, plural, one {# item} other {# items}}"
```
