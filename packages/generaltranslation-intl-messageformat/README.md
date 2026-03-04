# generaltranslation-intl-messageformat

ICU MessageFormat formatter with locale-aware plural and select rules. Python equivalent of [`intl-messageformat`](https://www.npmjs.com/package/intl-messageformat).

Uses [`generaltranslation-icu-messageformat-parser`](../generaltranslation-icu-messageformat-parser) for parsing and [Babel](https://babel.pocoo.org/) for CLDR plural rules.

## Installation

```bash
pip install generaltranslation-intl-messageformat
```

Dependencies: `generaltranslation-icu-messageformat-parser`, `babel>=2.18.0`. Pure Python, no C extensions.

## Quick Start

```python
from generaltranslation_intl_messageformat import IntlMessageFormat

# Simple variable interpolation
mf = IntlMessageFormat("Hello, {name}!", "en")
mf.format({"name": "World"})  # "Hello, World!"

# Plural with CLDR rules
mf = IntlMessageFormat("{count, plural, one {# item} other {# items}}", "en")
mf.format({"count": 1})   # "1 item"
mf.format({"count": 5})   # "5 items"
mf.format({"count": 1000})  # "1,000 items"

# Select
mf = IntlMessageFormat("{gender, select, male {He} female {She} other {They}} left.", "en")
mf.format({"gender": "female"})  # "She left."

# Selectordinal
mf = IntlMessageFormat("{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}", "en")
mf.format({"n": 1})   # "1st"
mf.format({"n": 22})  # "22nd"
mf.format({"n": 3})   # "3rd"
mf.format({"n": 4})   # "4th"
```

## API

### `IntlMessageFormat(pattern, locale="en")`

Create a message formatter.

**Args:**
- `pattern` (`str`): An ICU MessageFormat pattern string.
- `locale` (`str`): A BCP 47 locale tag. Defaults to `"en"`. Falls back to `"en"` if the locale is invalid.

### `IntlMessageFormat.format(values=None)`

Format the message with variable values.

**Args:**
- `values` (`dict | None`): A dict mapping variable names to values. Values can be `str`, `int`, `float`, or any type convertible via `str()`. Missing variables resolve to empty string.

**Returns:** `str` — The formatted message.

### `IntlMessageFormat.pattern`

**Type:** `str` — The original pattern string (read-only property).

### `IntlMessageFormat.locale`

**Type:** `babel.Locale` — The resolved Babel locale (read-only property).

## Supported ICU Features

### Simple variables
```python
IntlMessageFormat("Hello, {name}!", "en").format({"name": "World"})
# "Hello, World!"
```

### Plural
Selects a branch based on CLDR plural rules for the locale. Supports `one`, `two`, `few`, `many`, `other`, and `zero` categories, plus exact matches with `=N`.

```python
# English: one/other
IntlMessageFormat("{n, plural, one {# dog} other {# dogs}}", "en").format({"n": 1})
# "1 dog"

# Arabic: zero/one/two/few/many/other
IntlMessageFormat(
    "{n, plural, zero {صفر} one {واحد} two {اثنان} few {# قليل} many {# كثير} other {# آخر}}", "ar"
).format({"n": 3})
# "3 قليل"

# Russian: one/few/many/other
IntlMessageFormat(
    "{n, plural, one {# книга} few {# книги} many {# книг} other {# книг}}", "ru"
).format({"n": 21})
# "21 книга"
```

### Exact match
```python
IntlMessageFormat(
    "{n, plural, =0 {no items} =1 {one item} other {# items}}", "en"
).format({"n": 0})
# "no items"
```

### Plural with offset
The `offset` value is subtracted before plural rule evaluation. The `#` hash displays the offset-adjusted value.

```python
IntlMessageFormat(
    "{guests, plural, offset:1 =0 {nobody} =1 {{host}} one {{host} and # other} other {{host} and # others}}", "en"
).format({"guests": 3, "host": "Alice"})
# "Alice and 2 others"
```

### Selectordinal
Selects a branch based on CLDR ordinal plural rules.

```python
IntlMessageFormat(
    "{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}", "en"
).format({"n": 23})
# "23rd"
```

### Select
Matches a string value to a branch key, falls back to `other`.

```python
IntlMessageFormat(
    "{type, select, cat {meow} dog {woof} other {???}}", "en"
).format({"type": "cat"})
# "meow"
```

### Nested expressions
Plural inside select, select inside plural, variables inside branches — all work.

```python
IntlMessageFormat(
    "{gender, select, male {He has {n, plural, one {# item} other {# items}}} other {They have {n, plural, one {# item} other {# items}}}}", "en"
).format({"gender": "male", "n": 1})
# "He has 1 item"
```

### Hash `#` replacement
Inside plural/selectordinal branches, `#` is replaced with the numeric value (locale-formatted with grouping separators).

```python
IntlMessageFormat("{n, plural, other {# items}}", "en").format({"n": 1000})
# "1,000 items"

IntlMessageFormat("{n, plural, other {# Artikel}}", "de").format({"n": 1000})
# "1.000 Artikel"
```

## Locale Support

Uses Babel's CLDR data for plural rules, covering 100+ locales. Tested against `icu4py` (ICU4C bindings) for correctness across:

- **English** (en) — one/other
- **French** (fr) — one/other (0 is "one")
- **German** (de) — one/other
- **Arabic** (ar) — zero/one/two/few/many/other
- **Russian** (ru) — one/few/many/other
- **Polish** (pl) — one/few/many/other
- **Japanese** (ja) — other only
- And all other locales supported by Babel/CLDR

## Known Carve-outs

- **Boolean values**: Python `True`/`False` are formatted as `"True"`/`"False"` (Python convention). ICU4C formats them as `1`/`0`.
- **Escape sequences**: `''` and `'{...}'` are unescaped during parsing (matching `@formatjs/icu-messageformat-parser` behavior). The formatted output contains the unescaped text.
