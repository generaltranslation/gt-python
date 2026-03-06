from generaltranslation.static._condense_vars import condense_vars
from generaltranslation.static._constants import VAR_IDENTIFIER, VAR_NAME_IDENTIFIER
from generaltranslation.static._declare_static import declare_static
from generaltranslation.static._declare_var import declare_var
from generaltranslation.static._decode_vars import decode_vars
from generaltranslation.static._extract_vars import extract_vars
from generaltranslation.static._index_vars import index_vars
from generaltranslation.static._sanitize_var import sanitize_var

__all__ = [
    "VAR_IDENTIFIER",
    "VAR_NAME_IDENTIFIER",
    "sanitize_var",
    "declare_var",
    "declare_static",
    "decode_vars",
    "extract_vars",
    "index_vars",
    "condense_vars",
]
