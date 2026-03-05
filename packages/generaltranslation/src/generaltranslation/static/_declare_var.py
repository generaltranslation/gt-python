from __future__ import annotations

from generaltranslation.static._constants import VAR_IDENTIFIER, VAR_NAME_IDENTIFIER
from generaltranslation.static._sanitize_var import sanitize_var


def declare_var(
    variable: str | int | float | bool | None,
    *,
    name: str | None = None,
) -> str:
    """Mark a value as a non-translatable variable in an ICU string.

    Args:
        variable: The value to embed.
        name: Optional human-readable variable name.

    Returns:
        An ICU ``{_gt_, select, other {…}}`` construct.
    """
    if variable is None:
        raw = ""
    elif isinstance(variable, bool):
        raw = str(variable).lower()
    else:
        raw = str(variable)
    sanitized_variable = sanitize_var(raw)
    variable_section = f" other {{{sanitized_variable}}}"

    name_section = ""
    if name:
        sanitized_name = sanitize_var(name)
        name_section = f" {VAR_NAME_IDENTIFIER} {{{sanitized_name}}}"

    return f"{{{VAR_IDENTIFIER}, select,{variable_section}{name_section}}}"
