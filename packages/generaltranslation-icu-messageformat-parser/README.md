# generaltranslation-icu-messageformat-parser

> ⚠️ **Experimental / Unstable** — This package is under active development and may be subject to breaking changes.

A pure-Python ICU MessageFormat parser with whitespace-preserving AST and string reconstruction. Python equivalent of [`@formatjs/icu-messageformat-parser`](https://www.npmjs.com/package/@formatjs/icu-messageformat-parser).

Derived from [pyicumessageformat](https://github.com/SirStendec/pyicumessageformat) by Mike deBeaubien (MIT license).

## Installation

```bash
pip install generaltranslation-icu-messageformat-parser
```

No dependencies. Pure Python. Requires Python 3.10+.

## Quick Start

```python
from generaltranslation_icu_messageformat_parser import Parser, print_ast

parser = Parser()
ast = parser.parse("{count, plural, one {# item} other {# items}}")
# [{'name': 'count', 'type': 'plural', 'offset': 0, 'options': {'one': [{'type': 'number', 'name': 'count', 'hash': True}, ' item'], 'other': [{'type': 'number', 'name': 'count', 'hash': True}, ' items']}}]
```

## API

### `Parser(options=None)`

Create a parser instance with optional configuration.

**Options dict keys:**

| Option | Type | Default | Description |
|---|---|---|---|
| `subnumeric_types` | `list[str]` | `['plural', 'selectordinal']` | Types that support `#` hash replacement |
| `submessage_types` | `list[str]` | `['plural', 'selectordinal', 'select']` | Types with sub-message branches |
| `maximum_depth` | `int` | `50` | Maximum nesting depth |
| `allow_tags` | `bool` | `False` | Enable XML-style `<tag>` parsing |
| `strict_tags` | `bool` | `False` | Strict tag parsing mode |
| `tag_prefix` | `str \| None` | `None` | Required tag name prefix |
| `tag_type` | `str` | `'tag'` | AST node type string for tags |
| `include_indices` | `bool` | `False` | Include `start`/`end` positions in AST nodes |
| `loose_submessages` | `bool` | `False` | Allow loose submessage parsing |
| `allow_format_spaces` | `bool` | `True` | Allow spaces in format strings |
| `require_other` | `bool` | `True` | Require `other` branch in plural/select |
| `preserve_whitespace` | `bool` | `False` | Store whitespace in `_ws` dict on AST nodes for lossless round-trips |

### `Parser.parse(input, tokens=None)`

Parse an ICU MessageFormat string into an AST.

**Args:**
- `input` (`str`): The ICU MessageFormat string to parse.
- `tokens` (`list | None`): Optional list to populate with token objects for low-level analysis.

**Returns:** `list` — A list of AST nodes (strings and dicts).

**Raises:** `SyntaxError` on malformed input, `TypeError` if input is not a string.

### `print_ast(ast)`

Reconstruct an ICU MessageFormat string from an AST.

**Args:**
- `ast` (`list`): The AST as returned by `Parser.parse()`.

**Returns:** `str` — The reconstructed ICU MessageFormat string.

When the AST contains `_ws` whitespace metadata (from `preserve_whitespace=True`), reconstruction is lossless — the output exactly matches the original input. Without whitespace metadata, normalized spacing is used.

## AST Node Types

### String literal
Plain strings appear directly in the AST list:
```python
parser.parse("Hello world")
# ["Hello world"]
```

### Simple variable `{name}`
```python
{"name": "username"}
```

### Typed placeholder `{name, type, style}`
```python
{"name": "amount", "type": "number", "format": "::currency/USD"}
```

### Plural / selectordinal `{n, plural, ...}`
```python
{
    "name": "count",
    "type": "plural",          # or "selectordinal"
    "offset": 0,               # offset value (0 if none)
    "options": {
        "one": [{"type": "number", "name": "count", "hash": True}, " item"],
        "other": [{"type": "number", "name": "count", "hash": True}, " items"],
        "=0": ["no items"],    # exact match keys
    }
}
```

### Select `{gender, select, ...}`
```python
{
    "name": "gender",
    "type": "select",
    "options": {
        "male": ["He"],
        "female": ["She"],
        "other": ["They"],
    }
}
```

### Hash `#` (inside plural/selectordinal)
```python
{"type": "number", "name": "count", "hash": True}
```

### With `include_indices=True`
All dict nodes gain `start` and `end` integer fields indicating byte positions in the original string.

### With `preserve_whitespace=True`
Dict nodes gain a `_ws` dict storing whitespace at each structural position, enabling lossless `print_ast()` round-trips.

## Supported ICU Features

- Simple variable interpolation: `{name}`
- Plural with CLDR categories: `{n, plural, one {...} other {...}}`
- Exact match: `{n, plural, =0 {...} =1 {...} other {...}}`
- Plural offset: `{n, plural, offset:1 ...}`
- Selectordinal: `{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}`
- Select: `{gender, select, male {...} female {...} other {...}}`
- Nested expressions: plural inside select, select inside plural, etc.
- Typed placeholders: `{amount, number}`, `{d, date, short}`
- ICU escape sequences: `''` for literal quote, `'{...}'` for literal braces
- Hash `#` replacement inside plural/selectordinal branches
- XML-style tags (opt-in): `<bold>text</bold>`

## Known Limitations

- **Escape sequences are consumed during parsing.** `''` becomes `'` and `'{...}'` becomes `{...}` in the AST. These cannot be reconstructed by `print_ast()`. This matches the behavior of `@formatjs/icu-messageformat-parser`.
