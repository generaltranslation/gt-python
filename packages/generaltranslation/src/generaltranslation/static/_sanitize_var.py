import re


def sanitize_var(string: str) -> str:
    """Sanitize a string so it can be safely embedded in ICU select syntax.

    Escapes ICU special characters by:
    1. Doubling all ASCII single quotes (U+0027)
    2. Wrapping the region containing special characters ({}<>) in single quotes
    """
    # Double all ASCII single quotes (U+0027 only)
    result = string.replace("'", "''")

    # Find first special character position
    special = re.compile(r"[{}<>]")
    match = special.search(result)
    if match is None:
        return result

    first_special_index = match.start()

    # Find last special character position
    last_special_index = -1
    for i in range(len(result) - 1, -1, -1):
        if result[i] in "{}<>":
            last_special_index = i
            break

    # Wrap the special character region in single quotes
    result = (
        result[:first_special_index]
        + "'"
        + result[first_special_index : last_special_index + 1]
        + "'"
        + result[last_special_index + 1 :]
    )

    return result
