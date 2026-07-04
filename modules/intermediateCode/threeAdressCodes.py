"""
Three-Address Code Generator.

Produces a flat list of quadruples: (op, arg1, arg2, result).

Because your Condition AST is recursive (mirroring the grammar's right
recursion: `id relop expr [logop Condition]`), short-circuit &&/|| codegen
falls out of straightforward recursion instead of needing the classic
Dragon-Book on-the-fly backpatch lists (those exist to handle single-pass
bottom-up parsing where you don't have the whole expression in hand yet --
we do, since we're generating from a complete AST).

Semantics: `a && b || c` parses right-associatively per the grammar, i.e.
as `a && (b || c)`. Each Condition node either jumps to true_label (if it
and everything after it up the chain succeeds) or false_label.
"""

from modules.astBuilder.astNodes import (
    Declaration, Assign, Return, If, Id, Num, Dec, Letter, BinOp,
)


class TACGenerator:

    def __init__(self):
        self.code = []          # list of (op, arg1, arg2, result)
        self.temp_count = 0
        self.label_count = 0

    # ------------------------------------------------------------- utils --
    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, arg1=None, arg2=None, result=None):
        idx = len(self.code)
        self.code.append((op, arg1, arg2, result))
        return idx

    def pretty(self):
        lines = []
        for i, (op, a1, a2, res) in enumerate(self.code):
            if op == "label":
                lines.append(f"{a1}:")
            elif op == "goto":
                lines.append(f"    goto {a1}")
            elif op in ("if_true", "if_false"):
                lines.append(f"    {op} {a1} goto {res}")
            elif op in ("func_begin", "func_end"):
                lines.append(f"{op} {a1}")
            elif op == "return":
                lines.append(f"    return {a1 if a1 is not None else ''}")
            elif op == "=":
                lines.append(f"    {res} = {a1}")
            elif res is not None and a2 is not None:
                lines.append(f"    {res} = {a1} {op} {a2}")
            elif res is not None:
                lines.append(f"    {res} = {op} {a1}")
            else:
                lines.append(f"    ({op}, {a1}, {a2}, {res})")
        return "\n".join(lines)

    # --------------------------------------------------------------- API --
    def generate(self, program):
        for func in program.functions:
            self.gen_function(func)
        return self.code

    # ----------------------------------------------------------- program --
    def gen_function(self, func):
        self.emit("func_begin", func.name)
        for stmt in func.body:
            self.gen_stmt(stmt)
        self.emit("func_end", func.name)

    def gen_stmt(self, stmt):
        method = getattr(self, f"gen_{type(stmt).__name__}", None)
        if method is not None:
            method(stmt)

    def gen_Declaration(self, node: Declaration):
        pass  # storage already assigned by MemoryManager; no runtime code needed

    def gen_Assign(self, node: Assign):
        place = self.gen_expr(node.expr)
        self.emit("=", place, None, node.name)

    def gen_Return(self, node: Return):
        if node.value is not None:
            place = self.gen_expr(node.value)
            self.emit("return", place)
        else:
            self.emit("return")

    # -------------------------------------------------------- expressions --
    def gen_expr(self, node):
        if isinstance(node, Id):
            return node.name
        if isinstance(node, (Num, Dec, Letter)):
            return str(node.value)
        if isinstance(node, BinOp):
            left = self.gen_expr(node.left)
            right = self.gen_expr(node.right)
            t = self.new_temp()
            self.emit(node.op, left, right, t)
            return t
        return None

    # ----------------------------------------------------- control flow ---
    def gen_If(self, node: If):
        end_label = self.new_label()
        self.gen_if_branch(node.condition, node.then_body, end_label)
        for cond, body in node.elifs:
            self.gen_if_branch(cond, body, end_label)
        if node.else_body:
            for s in node.else_body:
                self.gen_stmt(s)
        self.emit("label", end_label)

    def gen_if_branch(self, cond, body, end_label):
        body_label = self.new_label()
        false_label = self.new_label()
        self.gen_condition(cond, body_label, false_label)
        self.emit("label", body_label)
        for s in body:
            self.gen_stmt(s)
        self.emit("goto", end_label)
        self.emit("label", false_label)

    def gen_condition(self, cond, true_label, false_label):
        """Emit code that jumps to true_label if `cond` holds, false_label
        otherwise. Recurses down `cond.rest` for &&/|| short-circuiting."""
        right = self.gen_expr(cond.expr)
        t = self.new_temp()
        self.emit(cond.relop, cond.id_name, right, t)

        if cond.rest is None:
            self.emit("if_true", t, None, true_label)
            self.emit("if_false", t, None, false_label)
            return

        if cond.logop == "&&":
            # this term false => whole chain false; else fall through and check the rest
            self.emit("if_false", t, None, false_label)
            self.gen_condition(cond.rest, true_label, false_label)
        elif cond.logop == "||":
            # this term true => whole chain true; else fall through and check the rest
            self.emit("if_true", t, None, true_label)
            self.gen_condition(cond.rest, true_label, false_label)
