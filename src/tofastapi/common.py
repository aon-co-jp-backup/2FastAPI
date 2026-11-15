"""Shared helpers for the Flask / Django -> FastAPI converters (libcst based, comments and formatting are preserved)."""
from __future__ import annotations

import dataclasses
import re
from typing import List, Optional

import libcst as cst


@dataclasses.dataclass
class Warn:
    line: int
    code: str
    msg: str

    def __str__(self) -> str:
        return "line %d: [%s] %s" % (self.line, self.code, self.msg)


@dataclasses.dataclass
class Result:
    code: str
    warnings: List[Warn]
    routes: int = 0


def dotted(node: cst.CSTNode) -> Optional[str]:
    """`request.args.get` -> "request.args.get" for Name/Attribute chains, else None."""
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        left = dotted(node.value)
        if left is None:
            return None
        return left + "." + node.attr.value
    return None


def str_value(node: Optional[cst.CSTNode]) -> Optional[str]:
    """Python value of a plain string literal node, else None."""
    if isinstance(node, cst.SimpleString):
        try:
            v = node.evaluated_value
        except Exception:
            return None
        return v if isinstance(v, str) else None
    if isinstance(node, cst.ConcatenatedString):
        a, b = str_value(node.left), str_value(node.right)
        return a + b if a is not None and b is not None else None
    return None


def is_stringish(node: cst.CSTNode) -> bool:
    """Expressions that are certainly `str` (so Flask/Django would send them as text/html)."""
    if isinstance(node, (cst.SimpleString, cst.ConcatenatedString, cst.FormattedString)):
        return True
    if isinstance(node, cst.BinaryOperation):
        return is_stringish(node.left) or is_stringish(node.right) if isinstance(node.operator, (cst.Add, cst.Modulo)) else False
    if isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute) and node.func.attr.value in ("format", "join", "upper", "lower", "strip"):
        return True
    return False


def ident(key: str) -> str:
    """A query/form/header key as a valid Python identifier."""
    n = re.sub(r"\W", "_", key)
    if not n or n[0].isdigit():
        n = "p_" + n
    return n


PATH_CONV = {"int": "int", "float": "float", "string": "str", "str": "str", "path": "str", "uuid": "uuid.UUID", "any": "str"}
_RULE = re.compile(r"<(?:(\w+)(?:\([^)]*\))?:)?(\w+)>")


def convert_rule(rule: str):
    """Flask/Django-style `/a/<int:id>/<name>` -> (`/a/{id}/{name}`, [(name, annotation)...])."""
    params = []

    def sub(m):
        conv, name = m.group(1) or "string", m.group(2)
        params.append((name, PATH_CONV.get(conv, "str")))
        return "{%s:path}" % name if conv == "path" else "{%s}" % name

    return _RULE.sub(sub, rule), params


def make_param(name: str, annotation: Optional[str], default: Optional[str]) -> cst.Param:
    return cst.Param(
        name=cst.Name(name),
        annotation=cst.Annotation(cst.parse_expression(annotation)) if annotation else None,
        default=cst.parse_expression(default) if default is not None else None,
    )


def order_params(params: List[cst.Param]) -> List[cst.Param]:
    """Parameters without defaults must come first."""
    return [p for p in params if p.default is None] + [p for p in params if p.default is not None]


class ParamSet:
    """Extra parameters collected while rewriting a view body (de-duplicated by name)."""

    def __init__(self):
        self.items = {}  # name -> (annotation, default)
        self.order = []

    def add(self, name: str, annotation: str, default: Optional[str]):
        if name not in self.items:
            self.items[name] = (annotation, default)
            self.order.append(name)
        return name

    def params(self):
        return [make_param(n, self.items[n][0], self.items[n][1]) for n in self.order]


def count_name(node: cst.CSTNode, name: str) -> int:
    """How many times `name` is read as a bare identifier below `node`."""
    found = [0]

    class V(cst.CSTVisitor):
        def visit_Name(self, n: cst.Name):
            if n.value == name:
                found[0] += 1

        def visit_Attribute(self, n: cst.Attribute):
            # `x.request` is an attribute name, not a variable read
            n.value.visit(self)
            return False

        def visit_Arg(self, n: cst.Arg):
            if n.keyword is not None:
                n.value.visit(self)
                return False

    node.visit(V())
    return found[0]
