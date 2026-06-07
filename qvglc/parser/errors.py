from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiagnosticCode(str, Enum):
    PARSE_SYNTAX = "parse_syntax"
    UNKNOWN_IMPORT = "unknown_import"
    UNKNOWN_TYPE = "unknown_type"
    UNKNOWN_PROPERTY = "unknown_property"
    UNSUPPORTED_EXPR = "unsupported_expr"
    UNSUPPORTED_FEATURE = "unsupported_feature"
    UNSUPPORTED_ANCHOR = "unsupported_anchor"


@dataclass
class QvglDiagnostic(Exception):
    code: DiagnosticCode
    message: str
    line: int = 0
    column: int = 0

    def __str__(self) -> str:
        loc = f"{self.line}:{self.column}: " if self.line else ""
        return f"{loc}{self.code.value}: {self.message}"
