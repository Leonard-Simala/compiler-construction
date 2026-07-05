"""
=============================================================================
Module      : astNodes.py
Description :
Author      : Leonard Simala
Date        : 2023-04-03
Version     : 1.0.0
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any


# ---------------------------------------------------------------- Program --
@dataclass
class Program:
    functions: List["Function"] = field(default_factory=list)


@dataclass
class Param:
    name: str
    type: str
    line: Optional[int] = None


@dataclass
class Function:
    name: str
    ret_type: str
    params: List[Param]
    body: List[Any]
    is_main: bool = False
    line: Optional[int] = None
    frame_size: Optional[int] = None   # filled in by MemoryManager


# ------------------------------------------------------------- Statements --
@dataclass
class Declaration:
    type: str
    names: List[str]
    line: Optional[int] = None


@dataclass
class Assign:
    name: str
    expr: Any
    type: Optional[str] = None
    line: Optional[int] = None


@dataclass
class Return:
    value: Optional[Any]
    line: Optional[int] = None


@dataclass
class If:
    condition: "Condition"
    then_body: List[Any]
    elifs: List[Tuple["Condition", List[Any]]] = field(default_factory=list)
    else_body: Optional[List[Any]] = None
    line: Optional[int] = None


# right-recursive, mirrors: Condition -> ID Rel-op Expression Compound-condition
#                           Compound-condition -> Log-op Condition | EPSILON
@dataclass
class Condition:
    id_name: str
    relop: str
    expr: Any
    logop: Optional[str] = None          # "&&" / "||" joining to `rest`, or None
    rest: Optional["Condition"] = None
    line: Optional[int] = None


# ------------------------------------------------------------- Expressions -
@dataclass
class BinOp:
    op: str          # '+', '-', '*', '/'
    left: Any
    right: Any
    type: Optional[str] = None
    line: Optional[int] = None


@dataclass
class Id:
    name: str
    type: Optional[str] = None
    line: Optional[int] = None


@dataclass
class Num:
    value: str
    type: Optional[str] = None
    line: Optional[int] = None


@dataclass
class Dec:
    value: str
    type: Optional[str] = None
    line: Optional[int] = None


@dataclass
class Letter:
    value: str
    type: Optional[str] = None
    line: Optional[int] = None
