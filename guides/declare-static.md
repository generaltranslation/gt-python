# Using `declare_static`

`declare_static` marks content as statically analyzable so that the GT CLI can extract all possible translation entries at build time.

## Overview

`declare_static` is an identity function — it returns exactly what you pass in. Its purpose is as a **marker** for static analysis tools. When the GT CLI scans your code, it recognizes `declare_static(...)` calls and determines all possible return values, creating a separate translation entry for each.

This is useful for:
- **Preserving word agreement** across languages (gender, plurality, etc.)
- **Reusable content** with function calls inside translated strings
- **Fragmented sentences** where part of the string is dynamic but has a known set of outcomes

## Installation

`declare_static` is exported from all GT Python packages:

```python
from gt_fastapi import declare_static
# or
from gt_flask import declare_static
# or
from gt_i18n import declare_static
```

## Basic usage

```python
from gt_fastapi import declare_static, t

def get_subject(gender: str) -> str:
    return "boy" if gender == "male" else "girl"

# Without declare_static — the CLI can't know the possible values
message = t(f"The {get_subject(gender)} is playing.")

# With declare_static — the CLI extracts both outcomes
message = t(f"The {declare_static(get_subject(gender))} is playing.")
```

With `declare_static`, the CLI creates two translation entries:
- `"The boy is playing."` → `"El niño está jugando."`
- `"The girl is playing."` → `"La niña está jugando."`

Notice how agreement is handled automatically — Spanish uses "El" vs "La" depending on the subject.

## How it works

1. **At build time**, the GT CLI analyzes functions wrapped by `declare_static`
2. It determines all possible return values (these must be statically analyzable)
3. It creates separate translation entries for each unique outcome
4. **At runtime**, `declare_static` is just an identity function — it returns its argument unchanged

## Combining with `declare_var`

Use `declare_var` for truly dynamic content (user input, API data) inside a `declare_static` call:

```python
from gt_fastapi import declare_static, declare_var, t

def get_greeting(name: str | None) -> str:
    if name:
        return f"Hello, {declare_var(name)}"
    return "Hello, stranger"

message = t(f"{declare_static(get_greeting(name))}! How are you?")
```

## Inline expressions

You can embed logic directly:

```python
from gt_fastapi import declare_static, t

message = t(f"The {declare_static('boy' if gender == 'male' else 'girl')} is playing.")
```

## Performance considerations

`declare_static` multiplies translation entries. Each call with N possible outcomes creates N entries, and multiple `declare_static` calls in the same string multiply exponentially. Use judiciously.

## Notes

- All possible outcomes must be statically analyzable at build time
- Dynamic content (variables, API calls) inside `declare_static` should be wrapped with `declare_var`
- `decode_vars` can be used to extract original values from declared variables
