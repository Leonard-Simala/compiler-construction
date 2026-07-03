"""
Three Address Code (TAC) Generator
====================================
Walks the parse tree produced by the parser and emits TAC instructions.
Node names in the tree match the non-terminals in the grammar exactly.

Productions reference (key ones):
  23 : Assign-stmt       → ID = Expression ;
  20 : Declaration-stmt  → Type-specifier ID Declaration-Id
  36 : Conditional-stmt  → if ( Condition ) Statement-body Conditional-nest
  37 : Condition         → ID Rel-op Expression Compound-condition
  38 : Compound-condition→ Log-op Condition
  57 : Return-stmt       → return Return-type ;
  24 : Expression        → Term Term-op
  26 : Term              → Factor
  27 : Term-op           → + Expression
  28 : Term-op           → - Expression
  30 : Term-op           → * Factor
  31 : Term-op           → / Factor
"""

from anytree import PreOrderIter


class TACGenerator:
    def __init__(self, parse_tree, memory_manager=None):
        self.parse_tree = parse_tree
        self.memory = memory_manager
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    # ── Helpers ────────────────────────────────────────────────────────────────

    def new_temp(self):
        self.temp_count += 1
        t = f"t{self.temp_count}"
        if self.memory:
            self.memory.allocate_temp(t)
        return t

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instruction):
        self.code.append(instruction)

    def save(self, filepath):
        with open(filepath, "w") as f:
            for line in self.code:
                f.write(line + "\n")
        print(f"[TAC] Saved to {filepath}")

    def _token_of(self, node):
        """Return the token string of a leaf node."""
        if hasattr(node, "token"):
            return str(node.token).strip()
        return str(node.name).strip()

    def _children(self, node):
        return list(node.children)

    # ── Entry point ────────────────────────────────────────────────────────────

    def generate(self):
        self._visit(self.parse_tree)
        return self.code

    # ── Main dispatcher ────────────────────────────────────────────────────────

    def _visit(self, node):
        """Dispatch to the correct handler based on node name."""
        if node is None:
            return None

        name = node.name

        dispatch = {
            "Program"            : self._program,
            "Main-function"      : self._function,
            "Function"           : self._function,
            "Function-body"      : self._function_body,
            "Statement-list"     : self._statement_list,
            "Statement"          : self._statement,
            "Declaration-stmt"   : self._declaration,
            "Assign-stmt"        : self._assignment,
            "Conditional-stmt"   : self._conditional,
            "Return-stmt"        : self._return_stmt,
            "Expression"         : self._expression,
            "Term"               : self._term,
            "Factor"             : self._factor,
            "Condition"          : self._condition,
        }

        handler = dispatch.get(name)
        if handler:
            return handler(node)

        # Default: recurse into children
        return self._visit_children(node)

    def _visit_children(self, node):
        result = None
        for child in self._children(node):
            result = self._visit(child)
        return result

    # ── Program / Function ─────────────────────────────────────────────────────

    def _program(self, node):
        self._visit_children(node)

    def _function(self, node):
        """Handles both Function and Main-function nodes."""
        # Find the function name from Function-initial → Type-specifier ID
        # Emit a function label then process the body
        func_name = self._extract_function_name(node)
        if func_name:
            self.emit(f"\n{func_name}:")
        self._visit_children(node)

    def _extract_function_name(self, node):
        """Walk children to find the ID token that is the function name."""
        for child in PreOrderIter(node):
            if child.name in ("Function-initial", "Main-func-initial"):
                grandchildren = self._children(child)
                for gc in grandchildren:
                    if gc.name == "ID" or (hasattr(gc, "token") and gc.name not in (
                        "void", "char", "int", "float", "main"
                    )):
                        return self._token_of(gc)
        return None

    def _function_body(self, node):
        self._visit_children(node)

    # ── Statement list ─────────────────────────────────────────────────────────

    def _statement_list(self, node):
        """Production 14: Statement Statement-list | EPSILON (15)"""
        self._visit_children(node)

    def _statement(self, node):
        """Productions 16-19: routes to the correct statement type."""
        self._visit_children(node)

    # ── Declaration ────────────────────────────────────────────────────────────

    def _declaration(self, node):
        """
        Production 20: Type-specifier ID Declaration-Id
        Declaration-Id → ; (21) | , ID Declaration-Id (22)
        Emits: declare <type> <var>
        """
        children = self._children(node)
        if not children:
            return

        # children[0] = Type-specifier, children[1] = ID, children[2] = Declaration-Id
        var_type = self._token_of(children[0]) if children else "?"
        if len(children) > 1:
            var_name = self._token_of(children[1])
            self.emit(f"declare {var_type} {var_name}")

            # Handle comma-separated declarations: , ID Declaration-Id
            if len(children) > 2:
                self._declaration_id(children[2], var_type)

    def _declaration_id(self, node, var_type):
        """Recurse through Declaration-Id for multiple variable declarations."""
        children = self._children(node)
        # Production 22: , ID Declaration-Id
        # children will have the comma token, ID, then another Declaration-Id
        for child in children:
            if child.name == "ID" or (hasattr(child, "token") and "," not in self._token_of(child)):
                token = self._token_of(child)
                if token not in (",", ";"):
                    self.emit(f"declare {var_type} {token}")
            elif child.name == "Declaration-Id":
                self._declaration_id(child, var_type)

    # ── Assignment ─────────────────────────────────────────────────────────────

    def _assignment(self, node):
        """
        Production 23: ID = Expression ;
        node children: [ID_leaf, '=', Expression, ';']
        """
        children = self._children(node)
        if not children:
            return

        # Find the LHS identifier (first leaf with a token)
        lhs = self._token_of(children[0])

        # Find the Expression node
        expr_node = next((c for c in children if c.name == "Expression"), None)
        if expr_node:
            rhs = self._expression(expr_node)
            self.emit(f"{lhs} = {rhs}")

    # ── Expression ─────────────────────────────────────────────────────────────

    def _expression(self, node):
        """
        Production 24: Term Term-op
        Production 25: LETTER
        """
        children = self._children(node)
        if not children:
            return self._token_of(node)

        # Production 25: LETTER node directly
        if node.name == "LETTER" or (len(children) == 1 and children[0].name == "LETTER"):
            return self._token_of(children[0]) if children else self._token_of(node)

        # Production 24: Term Term-op
        term_node   = next((c for c in children if c.name == "Term"), None)
        term_op     = next((c for c in children if c.name == "Term-op"), None)

        left = self._term(term_node) if term_node else self._token_of(children[0])

        if term_op and self._children(term_op):
            return self._term_op(term_op, left)

        return left

    def _term(self, node):
        """
        Production 26: Factor
        """
        if node is None:
            return "?"
        children = self._children(node)
        if not children:
            return self._token_of(node)

        factor_node = next((c for c in children if c.name == "Factor"), None)
        return self._factor(factor_node) if factor_node else self._token_of(children[0])

    def _factor(self, node):
        """
        Production 32: ID
        Production 33: NUMBER
        Production 34: DECIMAL
        Production 35: ( Expression )
        """
        if node is None:
            return "?"
        children = self._children(node)
        if not children:
            return self._token_of(node)

        # ( Expression )
        expr_node = next((c for c in children if c.name == "Expression"), None)
        if expr_node:
            inner = self._expression(expr_node)
            return inner  # parentheses don't need a new temp unless part of op

        # ID / NUMBER / DECIMAL leaf
        return self._token_of(children[0])

    def _term_op(self, node, left):
        """
        Production 27: + Expression
        Production 28: - Expression
        Production 29: EPSILON
        Production 30: * Factor
        Production 31: / Factor
        """
        children = self._children(node)
        if not children:
            return left  # EPSILON

        op_node  = children[0]
        op       = self._token_of(op_node)

        if op in ("+", "-"):
            # + Expression or - Expression
            expr_node = next((c for c in children if c.name == "Expression"), None)
            right = self._expression(expr_node) if expr_node else "?"
        elif op in ("*", "/"):
            # * Factor or / Factor
            factor_node = next((c for c in children if c.name == "Factor"), None)
            right = self._factor(factor_node) if factor_node else "?"
        else:
            return left

        temp = self.new_temp()
        self.emit(f"{temp} = {left} {op} {right}")
        return temp

    # ── Condition ──────────────────────────────────────────────────────────────

    def _condition(self, node):
        """
        Production 37: ID Rel-op Expression Compound-condition
        Returns a string like 'average >= 90' or a temp for compound conditions.
        """
        children = self._children(node)
        if not children:
            return "?"

        # ID
        lhs = self._token_of(children[0])

        # Rel-op
        rel_op_node = next((c for c in children if c.name == "Rel-op"), None)
        op = self._token_of(self._children(rel_op_node)[0]) if rel_op_node and self._children(rel_op_node) else "?"

        # Expression (RHS)
        expr_node = next((c for c in children if c.name == "Expression"), None)
        rhs = self._expression(expr_node) if expr_node else "?"

        base_condition = f"{lhs} {op} {rhs}"

        # Compound-condition (optional: && / || more conditions)
        compound = next((c for c in children if c.name == "Compound-condition"), None)
        if compound and self._children(compound):
            return self._compound_condition(compound, base_condition)

        return base_condition

    def _compound_condition(self, node, left_condition):
        """
        Production 38: Log-op Condition
        Production 39: EPSILON
        """
        children = self._children(node)
        if not children:
            return left_condition

        log_op_node = next((c for c in children if c.name == "Log-op"), None)
        cond_node   = next((c for c in children if c.name == "Condition"), None)

        if not log_op_node or not cond_node:
            return left_condition

        log_op        = self._token_of(self._children(log_op_node)[0]) if self._children(log_op_node) else "&&"
        right_cond    = self._condition(cond_node)

        temp = self.new_temp()
        self.emit(f"{temp} = {left_condition} {log_op} {right_cond}")
        return temp

    # ── Conditional (if / else if / else) ──────────────────────────────────────

    def _conditional(self, node):
        """
        Production 36: if ( Condition ) Statement-body Conditional-nest
        """
        children = self._children(node)

        cond_node    = next((c for c in children if c.name == "Condition"), None)
        body_node    = next((c for c in children if c.name == "Statement-body"), None)
        nest_node    = next((c for c in children if c.name == "Conditional-nest"), None)

        true_label  = self.new_label()
        false_label = self.new_label()
        end_label   = self.new_label()

        # Evaluate condition
        condition = self._condition(cond_node) if cond_node else "?"

        self.emit(f"if {condition} goto {true_label}")
        self.emit(f"goto {false_label}")

        # True branch
        self.emit(f"{true_label}:")
        if body_node:
            self._statement_body(body_node)
        self.emit(f"goto {end_label}")

        # False branch / else if / else
        self.emit(f"{false_label}:")
        if nest_node:
            self._conditional_nest(nest_node, end_label)

        self.emit(f"{end_label}:")

    def _statement_body(self, node):
        """
        Production 48: Statement
        Production 49: { Statement-list }
        """
        self._visit_children(node)

    def _conditional_nest(self, node, end_label):
        """
        Production 50: Condition-body
        Production 51: EPSILON
        """
        children = self._children(node)
        cond_body = next((c for c in children if c.name == "Condition-body"), None)
        if cond_body:
            self._condition_body(cond_body, end_label)

    def _condition_body(self, node, end_label):
        """
        Production 52: Elif-stmt
        Production 53: Else-stmt
        """
        children = self._children(node)
        elif_node = next((c for c in children if c.name == "Elif-stmt"), None)
        else_node = next((c for c in children if c.name == "Else-stmt"), None)

        if elif_node:
            self._elif_stmt(elif_node, end_label)
        elif else_node:
            self._else_stmt(else_node)

    def _elif_stmt(self, node, end_label):
        """
        Production 54: if ( Condition ) Statement-body else Conditional-nest
        """
        children = self._children(node)

        cond_node = next((c for c in children if c.name == "Condition"), None)
        body_node = next((c for c in children if c.name == "Statement-body"), None)
        nest_node = next((c for c in children if c.name == "Conditional-nest"), None)

        true_label  = self.new_label()
        false_label = self.new_label()

        condition = self._condition(cond_node) if cond_node else "?"

        self.emit(f"if {condition} goto {true_label}")
        self.emit(f"goto {false_label}")

        self.emit(f"{true_label}:")
        if body_node:
            self._statement_body(body_node)
        self.emit(f"goto {end_label}")

        self.emit(f"{false_label}:")
        if nest_node:
            self._conditional_nest(nest_node, end_label)

    def _else_stmt(self, node):
        """
        Production 56: else Statement-body
        """
        body_node = next((c for c in self._children(node) if c.name == "Statement-body"), None)
        if body_node:
            self._statement_body(body_node)

    # ── Return ─────────────────────────────────────────────────────────────────

    def _return_stmt(self, node):
        """
        Production 57: return Return-type ;
        """
        children = self._children(node)
        ret_node = next((c for c in children if c.name == "Return-type"), None)
        if ret_node:
            ret_children = self._children(ret_node)
            value = self._token_of(ret_children[0]) if ret_children else "?"
            self.emit(f"return {value}")
        else:
            self.emit("return")
