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

# gt-flask

> ⚠️ **Experimental / Unstable** — This package is under active development and may be subject to breaking changes.

Automatic i18n for Flask.

## Installation

```bash
pip install gt-flask
```

## Quick Start

```python
from flask import Flask
from gt_flask import initialize_gt, t

app = Flask(__name__)
initialize_gt(app, default_locale="en", locales=["en", "es", "fr"])

@app.route("/")
def hello():
    return t("Hello, world!")
```

See the [full documentation](https://generaltranslation.com/docs/python) for guides and API reference.
