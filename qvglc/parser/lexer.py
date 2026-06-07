from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator

from .errors import DiagnosticCode, QvglDiagnostic


class TokKind(Enum):
    EOF = auto()
    IMPORT = auto()
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    LBRACE = auto()
    RBRACE = auto()
    COLON = auto()
    DOT = auto()
    LPAREN = auto()
    RPAREN = auto()
    PLUS = auto()
    COMMA = auto()
    ON = auto()


@dataclass
class Token:
    kind: TokKind
    text: str
    line: int
    column: int


class Lexer:
    def __init__(self, src: str) -> None:
        self._src = src
        self._i = 0
        self._line = 1
        self._col = 1

    def tokens(self) -> Iterator[Token]:
        while True:
            self._skip_ws_and_comments()
            if self._at_end():
                yield Token(TokKind.EOF, "", self._line, self._col)
                return
            start_line, start_col = self._line, self._col
            ch = self._peek()
            if ch in "{}":
                self._advance()
                kind = TokKind.LBRACE if ch == "{" else TokKind.RBRACE
                yield Token(kind, ch, start_line, start_col)
                continue
            if ch == ":":
                self._advance()
                yield Token(TokKind.COLON, ch, start_line, start_col)
                continue
            if ch == ".":
                self._advance()
                yield Token(TokKind.DOT, ch, start_line, start_col)
                continue
            if ch == "(":
                self._advance()
                yield Token(TokKind.LPAREN, ch, start_line, start_col)
                continue
            if ch == ")":
                self._advance()
                yield Token(TokKind.RPAREN, ch, start_line, start_col)
                continue
            if ch == "+":
                self._advance()
                yield Token(TokKind.PLUS, ch, start_line, start_col)
                continue
            if ch == ",":
                self._advance()
                yield Token(TokKind.COMMA, ch, start_line, start_col)
                continue
            if ch in "\"'":
                yield self._string(ch, start_line, start_col)
                continue
            if ch.isdigit() or (ch == "-" and self._peek(1).isdigit()):
                yield self._number(start_line, start_col)
                continue
            if ch.isalpha() or ch == "_":
                yield self._ident_or_keyword(start_line, start_col)
                continue
            raise QvglDiagnostic(
                DiagnosticCode.PARSE_SYNTAX,
                f"unexpected character {ch!r}",
                start_line,
                start_col,
            )

    def _ident_or_keyword(self, line: int, col: int) -> Token:
        start = self._i
        while not self._at_end() and (self._peek().isalnum() or self._peek() in "._"):
            self._advance()
        text = self._src[start : self._i]
        if text == "import":
            return Token(TokKind.IMPORT, text, line, col)
        if text == "on":
            return Token(TokKind.ON, text, line, col)
        return Token(TokKind.IDENT, text, line, col)

    def _number(self, line: int, col: int) -> Token:
        start = self._i
        if self._peek() == "-":
            self._advance()
        while not self._at_end() and (self._peek().isdigit() or self._peek() == "."):
            self._advance()
        return Token(TokKind.NUMBER, self._src[start : self._i], line, col)

    def _string(self, quote: str, line: int, col: int) -> Token:
        self._advance()
        start = self._i
        while not self._at_end() and self._peek() != quote:
            if self._peek() == "\\":
                self._advance()
            self._advance()
        if self._at_end():
            raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "unterminated string", line, col)
        text = self._src[start : self._i]
        self._advance()
        return Token(TokKind.STRING, text, line, col)

    def _skip_ws_and_comments(self) -> None:
        while not self._at_end():
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
                continue
            if ch == "\n":
                self._advance()
                self._line += 1
                self._col = 1
                continue
            if ch == "/" and self._peek(1) == "/":
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._advance()
                self._advance()
                while not self._at_end() and not (self._peek() == "*" and self._peek(1) == "/"):
                    if self._peek() == "\n":
                        self._line += 1
                        self._col = 1
                    self._advance()
                if self._at_end():
                    raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "unterminated block comment", self._line, self._col)
                self._advance()
                self._advance()
                continue
            break

    def _at_end(self) -> bool:
        return self._i >= len(self._src)

    def _peek(self, off: int = 0) -> str:
        j = self._i + off
        return self._src[j] if j < len(self._src) else "\0"

    def _advance(self) -> None:
        if not self._at_end():
            if self._src[self._i] == "\n":
                self._line += 1
                self._col = 1
            else:
                self._col += 1
            self._i += 1
