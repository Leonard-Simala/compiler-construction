"""
Semantic Analyzer.

Single recursive-descent pass over the AST. For each function: pushes a new
scope, declares parameters, walks the body (declaring locals, type-checking
assignments/conditions/returns), then pops the scope and records the frame
size MemoryManager computed.

Integration with your existing SymbolTableManager:
  - `SymbolTableManager.scope_stack` already gets `func_row_idx + 1` pushed on
    function entry, so `get_enclosing_fun()` keeps working exactly as it does
    today.
  - New rows appended here carry extra fields your current `insert()` doesn't
    set (`role`, `type`, `size`, `offset`, `arity`, `params`) -- this doesn't
    break `insert()`/`findrow()`/`_exists()`, it just adds fields other parts
    of the pipeline (TAC generator) can read later.
  - ASSUMPTION: no other part of your pipeline currently pushes/pops
    `scope_stack` or appends declaration rows to `symbol_table` (e.g. from
    inside the scanner). If it does, tell me and I'll adjust so we don't
    double-manage scope.
"""

from modules.astBuilder.astNodes import (
    Declaration, Assign, Return, If, Condition, BinOp, Id, Num, Dec, Letter,
)
from modules.memory.memoryManager import MemoryManager
from modules.symbolTableManager.symbolTableManager import SymbolTableManager


class SemanticAnalyzer:

    NUMERIC_RANK = {"char": 0, "int": 1, "float": 2}

    def __init__(self):
        self.errors = []
        self.current_function = None   # Function node currently being analyzed

    # ---------------------------------------------------------------- API --
    def analyze(self, program):
        MemoryManager.reset()
        for func in program.functions:
            self.visit_function(func)
        return self.errors

    @property
    def error_report(self):
        if not self.errors:
            return "There is no semantic error.\n"
        return "".join(f"{e}\n" for e in self.errors)

    def error(self, line, msg):
        loc = f"#{line}" if line is not None else "#?"
        self.errors.append(f"{loc} : Semantic Error! {msg}")

    # ----------------------------------------------------------- functions --
    def visit_function(self, func):
        if func.name != "main" and SymbolTableManager.findrow(func.name) is not None:
            self.error(func.line, f'Redefinition of function "{func.name}"')

        SymbolTableManager.symbol_table.append({
            "lexim": func.name,
            "scope": SymbolTableManager.scope(),
            "role": "function",
            "type": func.ret_type,
            "arity": len(func.params),
            "params": [p.type for p in func.params],
        })
        func_row_idx = len(SymbolTableManager.symbol_table) - 1

        self.current_function = func
        MemoryManager.enter_function_scope()
        SymbolTableManager.scope_stack.append(func_row_idx + 1)

        for p in func.params:
            self.declare_variable(p.name, p.type, p.line, role="param")

        for stmt in func.body:
            self.visit_statement(stmt)

        func.frame_size = MemoryManager.exit_function_scope()
        SymbolTableManager.scope_stack.pop()
        self.current_function = None

    def declare_variable(self, name, vtype, line, role="var"):
        if SymbolTableManager._exists(name, SymbolTableManager.scope()):
            self.error(line, f'Redeclaration of "{name}"')
            return
        size = MemoryManager.size_of(vtype)
        offset = MemoryManager.allocate(size)
        SymbolTableManager.symbol_table.append({
            "lexim": name,
            "scope": SymbolTableManager.scope(),
            "role": role,
            "type": vtype,
            "size": size,
            "offset": offset,
        })

    # ---------------------------------------------------------- statements --
    def visit_statement(self, stmt):
        method = getattr(self, f"visit_{type(stmt).__name__}", None)
        if method is not None:
            method(stmt)

    def visit_Declaration(self, node: Declaration):
        for name in node.names:
            self.declare_variable(name, node.type, node.line)

    def visit_Assign(self, node: Assign):
        row = SymbolTableManager.findrow(node.name)
        if row is None:
            self.error(node.line, f'"{node.name}" is not declared')
            return
        expr_type = self.visit_expr(node.expr)
        if not self.assignable(row.get("type"), expr_type):
            self.error(node.line, f'Type mismatch: cannot assign {expr_type} to {row.get("type")}')
        node.type = row.get("type")

    def visit_Return(self, node: Return):
        rtype = self.visit_expr(node.value) if node.value is not None else "void"
        if self.current_function is not None:
            expected = self.current_function.ret_type
            if expected == "void" and node.value is not None:
                self.error(node.line, f'Function "{self.current_function.name}" is void, cannot return a value')
            elif expected != "void" and not self.assignable(expected, rtype):
                self.error(node.line, f'Return type mismatch: expected {expected}, got {rtype}')

    def visit_If(self, node: If):
        self.visit_condition(node.condition)
        self.visit_block(node.then_body)
        for cond, body in node.elifs:
            self.visit_condition(cond)
            self.visit_block(body)
        if node.else_body:
            self.visit_block(node.else_body)

    def visit_block(self, stmts):
        MemoryManager.enter_block_scope()
        for s in stmts:
            self.visit_statement(s)
        MemoryManager.exit_block_scope()

    def visit_condition(self, cond: Condition):
        row = SymbolTableManager.findrow(cond.id_name)
        if row is None:
            self.error(cond.line, f'"{cond.id_name}" is not declared')
        else:
            expr_type = self.visit_expr(cond.expr)
            if not self.comparable(row.get("type"), expr_type):
                self.error(cond.line, f'Cannot compare {row.get("type")} with {expr_type}')
        if cond.rest is not None:
            self.visit_condition(cond.rest)

    # ---------------------------------------------------------- expressions --
    def visit_expr(self, node):
        if isinstance(node, Id):
            row = SymbolTableManager.findrow(node.name)
            if row is None:
                self.error(node.line, f'"{node.name}" is not declared')
                node.type = "int"
            else:
                node.type = row.get("type")
            return node.type
        if isinstance(node, Num):
            node.type = "int"
            return node.type
        if isinstance(node, Dec):
            node.type = "float"
            return node.type
        if isinstance(node, Letter):
            node.type = "char"
            return node.type
        if isinstance(node, BinOp):
            lt = self.visit_expr(node.left)
            rt = self.visit_expr(node.right)
            node.type = self.result_type(lt, rt, node.line)
            return node.type
        return None

    def result_type(self, lt, rt, line):
        if lt not in self.NUMERIC_RANK or rt not in self.NUMERIC_RANK:
            self.error(line, f'Invalid operand types "{lt}", "{rt}"')
            return "int"
        return lt if self.NUMERIC_RANK[lt] >= self.NUMERIC_RANK[rt] else rt

    def assignable(self, target, src):
        return target in self.NUMERIC_RANK and src in self.NUMERIC_RANK

    def comparable(self, a, b):
        return a in self.NUMERIC_RANK and b in self.NUMERIC_RANK
