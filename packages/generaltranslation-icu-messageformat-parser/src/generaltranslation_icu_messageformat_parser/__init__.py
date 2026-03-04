"""ICU MessageFormat parser with whitespace-preserving AST and string reconstruction.

A Python equivalent of ``@formatjs/icu-messageformat-parser``. Parses ICU
MessageFormat strings into ASTs and reconstructs strings from ASTs.

Derived from `pyicumessageformat <https://github.com/SirStendec/pyicumessageformat>`_
by Mike deBeaubien (MIT license).
"""

from generaltranslation_icu_messageformat_parser._parser import Parser
from generaltranslation_icu_messageformat_parser._printer import print_ast

__all__ = ["Parser", "print_ast"]
