from __future__ import annotations

from typing import Any

from .ast import Document, Import, Loc, Object
from .errors import DiagnosticCode, QvglDiagnostic
from .lexer import Lexer, TokKind, Token


class Parser:
    def __init__(self, src: str) -> None:
        self._tokens = list(Lexer(src).tokens())
        self._pos = 0

    def parse(self) -> Document:
        doc = Document()
        while self._check(TokKind.IMPORT):
            doc.imports.append(self._parse_import())
        if self._at_end():
            raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "expected root object")
        doc.root = self._parse_object()
        if not self._at_end():
            raise QvglDiagnostic(
                DiagnosticCode.PARSE_SYNTAX,
                f"unexpected token {self._peek().text!r}",
                self._peek().line,
                self._peek().column,
            )
        return doc

    def _parse_import(self) -> Import:
        tok = self._advance()
        loc = Loc(tok.line, tok.column)
        mod = self._expect(TokKind.IDENT, "import module name").text
        ver = ""
        if self._check(TokKind.NUMBER):
            ver = self._advance().text
        return Import(mod, ver, loc)

    def _parse_object(self) -> Object:
        type_tok = self._expect(TokKind.IDENT, "object type name")
        obj = Object(type_name=type_tok.text, loc=Loc(type_tok.line, type_tok.column))
        self._expect(TokKind.LBRACE, "'{'")
        self._parse_object_members(obj)
        self._advance()
        return obj

    def _parse_object_body(self, type_name: str) -> Object:
        obj = Object(type_name=type_name, loc=Loc(self._peek().line, self._peek().column))
        self._expect(TokKind.LBRACE, "'{'")
        self._parse_object_members(obj)
        self._advance()
        return obj

    def _parse_object_members(self, obj: Object) -> None:
        while not self._check(TokKind.RBRACE):
            if self._check(TokKind.IDENT):
                name_tok = self._advance()
                if name_tok.text == "function":
                    raise QvglDiagnostic(
                        DiagnosticCode.UNSUPPORTED_FEATURE,
                        "QML functions are not supported (move logic to C/runtime)",
                        name_tok.line,
                        name_tok.column,
                    )
                if name_tok.text in ("required", "readonly"):
                    mod = name_tok.text
                    kw = self._expect(TokKind.IDENT, "'property' after modifier")
                    if kw.text != "property":
                        raise QvglDiagnostic(
                            DiagnosticCode.PARSE_SYNTAX,
                            f"expected 'property' after {mod!r}, got {kw.text!r}",
                            kw.line,
                            kw.column,
                        )
                    type_tok = self._expect(TokKind.IDENT, "property type")
                    prop_tok = self._expect(TokKind.IDENT, "property name")
                    self._expect(TokKind.COLON, "':'")
                    val, loc = self._parse_value()
                    obj.properties.append(
                        (f"property {mod} {type_tok.text} {prop_tok.text}", val, loc)
                    )
                    continue
                if name_tok.text == "property":
                    type_tok = self._expect(TokKind.IDENT, "property type")
                    prop_tok = self._expect(TokKind.IDENT, "property name")
                    self._expect(TokKind.COLON, "':'")
                    val, loc = self._parse_value()
                    obj.properties.append((f"property {type_tok.text} {prop_tok.text}", val, loc))
                    continue
                if self._check(TokKind.ON):
                    self._advance()
                    target_tok = self._expect(TokKind.IDENT, "animation property")
                    child = Object(type_name=name_tok.text, loc=Loc(name_tok.line, name_tok.column))
                    child.properties.append(("__on_property__", target_tok.text, Loc(target_tok.line, target_tok.column)))
                    self._expect(TokKind.LBRACE, "'{'")
                    self._parse_object_members(child)
                    self._expect(TokKind.RBRACE, "'}'")
                    obj.children.append(child)
                    continue
                if name_tok.text.startswith("on") and len(name_tok.text) > 2 and name_tok.text[2].isupper():
                    self._expect(TokKind.COLON, "':'")
                    val, loc = self._parse_value()
                    obj.properties.append((name_tok.text, val, loc))
                    continue
                if self._check(TokKind.LBRACE):
                    child = self._parse_object_body(type_name=name_tok.text)
                    obj.children.append(child)
                    continue
                self._expect(TokKind.COLON, "':'")
                val, loc = self._parse_value()
                if name_tok.text == "id":
                    obj.object_id = str(val) if isinstance(val, str) else str(val.get("name", ""))
                else:
                    obj.properties.append((name_tok.text, val, loc))
                continue
            if self._check(TokKind.ON):
                self._parse_signal_handler(obj)
                continue
            raise QvglDiagnostic(
                DiagnosticCode.PARSE_SYNTAX,
                "unexpected token in object",
                self._peek().line,
                self._peek().column,
            )

    def _parse_signal_handler(self, obj: Object) -> None:
        on_tok = self._advance()
        signal = self._expect(TokKind.IDENT, "signal name after 'on'").text
        self._expect(TokKind.COLON, "':'")
        val, loc = self._parse_value()
        key = f"on{signal.capitalize()}" if signal[0].islower() else f"on{signal}"
        if signal == "clicked":
            key = "onClicked"
        obj.properties.append((key, val, loc))

    def _parse_value(self) -> tuple[Any, Loc]:
        tok = self._peek()
        loc = Loc(tok.line, tok.column)
        if self._check(TokKind.STRING):
            return self._advance().text, loc
        if self._check(TokKind.NUMBER):
            text = self._advance().text
            return float(text) if "." in text else int(text), loc
        if self._check(TokKind.IDENT):
            ident = self._peek().text
            if ident == "true":
                self._advance()
                return True, loc
            if ident == "false":
                self._advance()
                return False, loc
            if self._pos + 1 < len(self._tokens) and self._tokens[self._pos + 1].kind == TokKind.LBRACE:
                type_name = self._advance().text
                return self._parse_object_body(type_name), loc
            return self._parse_expr(), loc
        raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "expected value", tok.line, tok.column)

    def _parse_expr(self) -> dict[str, Any]:
        node = self._parse_atom()
        while self._check(TokKind.PLUS):
            self._advance()
            rhs = self._parse_atom()
            node = {"op": "add", "left": node, "right": rhs}
        return node

    def _parse_atom(self) -> Any:
        tok = self._peek()
        if tok.kind == TokKind.STRING:
            return {"op": "const", "value": self._advance().text}
        if tok.kind == TokKind.NUMBER:
            t = self._advance().text
            v = float(t) if "." in t else int(t)
            return {"op": "const", "value": v}
        return self._parse_primary()

    def _parse_primary(self) -> Any:
        tok = self._advance()
        if tok.kind != TokKind.IDENT:
            raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "expected identifier", tok.line, tok.column)

        if self._check(TokKind.DOT):
            self._advance()
            member = self._expect(TokKind.IDENT, "member name").text
            if self._check(TokKind.LPAREN):
                self._advance()
                args: list[Any] = []
                if not self._check(TokKind.RPAREN):
                    args.append(self._parse_call_arg())
                    while self._check(TokKind.COMMA):
                        self._advance()
                        args.append(self._parse_call_arg())
                self._expect(TokKind.RPAREN, "')'")
                return {"op": "call", "callee": f"{tok.text}.{member}", "args": args}
            return {"op": "member", "base": tok.text, "member": member}

        if self._check(TokKind.LPAREN):
            self._advance()
            args = []
            if not self._check(TokKind.RPAREN):
                args.append(self._parse_call_arg())
                while self._check(TokKind.COMMA):
                    self._advance()
                    args.append(self._parse_call_arg())
            self._expect(TokKind.RPAREN, "')'")
            return {"op": "call", "callee": tok.text, "args": args}

        return {"op": "sym", "name": tok.text}

    def _parse_call_arg(self) -> Any:
        tok = self._peek()
        if tok.kind == TokKind.STRING:
            return {"op": "const", "value": self._advance().text}
        if tok.kind == TokKind.NUMBER:
            t = self._advance().text
            v = float(t) if "." in t else int(t)
            return {"op": "const", "value": v}
        if tok.kind == TokKind.IDENT:
            return self._parse_primary()
        raise QvglDiagnostic(DiagnosticCode.PARSE_SYNTAX, "expected argument", tok.line, tok.column)

    def _check(self, kind: TokKind) -> bool:
        return not self._at_end() and self._peek().kind == kind

    def _advance(self) -> Token:
        tok = self._peek()
        self._pos += 1
        return tok

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _at_end(self) -> bool:
        return self._peek().kind == TokKind.EOF

    def _expect(self, kind: TokKind, what: str) -> Token:
        if not self._check(kind):
            t = self._peek()
            raise QvglDiagnostic(
                DiagnosticCode.PARSE_SYNTAX,
                f"expected {what}, got {t.text!r}",
                t.line,
                t.column,
            )
        return self._advance()


def parse_qml(src: str) -> Document:
    return Parser(src).parse()
