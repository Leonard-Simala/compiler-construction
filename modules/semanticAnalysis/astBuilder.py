"""
Parse tree (anytree) -> AST converter.

Your parser builds one anytree Node per grammar symbol, in production order,
with terminal leaves carrying a `.token` attribute (set via
`self.stack[-1].token = self.scanner.token_to_str(token)` in Parser.parse()).

Because the grammar is LL(1) and the tree already encodes which alternative
was chosen at each step (there's no ambiguity left to resolve), converting is
just a structural walk: for each non-terminal, look at which children are
present and recurse -- no lookahead needed here, unlike in the parser itself.

NOTE on `terminal_text()`: I don't know the exact string format your
`scanner.token_to_str()` produces (e.g. "foo" vs "ID:foo" vs "(ID, foo)").
I've written a best-effort extractor below -- run this on a small test
program and if identifiers/numbers come out wrong, paste me one example line
of your token_to_str() output and I'll fix the parsing in one line.

NOTE on line numbers: I don't see line numbers attached to parse tree nodes
currently. If you want accurate line numbers in semantic error messages, the
easiest fix is to have Parser store `self.stack[-1].line = self.scanner.line_number`
next to where it sets `.token`. Until then, `line` fields below will be None.
"""

from modules.astBuilder.astNodes import (
    Program, Function, Param, Declaration, Assign, Return, If, Condition,
    BinOp, Id, Num, Dec, Letter,
)


# --------------------------------------------------------------- helpers --
def child_named(node, name):
    for c in node.children:
        if c.name == name:
            return c
    return None


def terminal_text(node):
    """Extract the actual lexeme from a terminal leaf node."""
    if node is None:
        return None
    tok = getattr(node, "token", None)
    if tok is None:
        return node.name  # keyword terminals like 'void', '+' etc. have no .token
    text = str(tok)
    if ":" in text:
        text = text.split(":", 1)[1]
    return text.strip().strip("()").strip()


def node_line(node):
    return getattr(node, "line", None)


# --------------------------------------------------------------- Program --
def build_program(root):
    main_node = child_named(root, "Main-function")
    flist_node = child_named(root, "Function-list")
    functions = [build_main(main_node)] if main_node else []
    if flist_node is not None:
        functions += build_function_list(flist_node)
    return Program(functions)


def build_function_list(node):
    if not node.children:
        return []
    func_node = child_named(node, "Function")
    rest_node = child_named(node, "Function-list")
    funcs = [build_function(func_node)] if func_node else []
    if rest_node is not None:
        funcs += build_function_list(rest_node)
    return funcs


def build_function(node):
    finit = child_named(node, "Function-initial")
    fbody = child_named(node, "Function-body")
    ret_type, name = build_function_initial(finit)
    params, stmts = build_function_body(fbody)
    return Function(name, ret_type, params, stmts, is_main=False, line=node_line(finit))


def build_function_initial(node):
    type_node = child_named(node, "Type-specifier")
    id_node = child_named(node, "ID")
    return build_type_specifier(type_node), terminal_text(id_node)


def build_type_specifier(node):
    return node.children[0].name  # 'void' | 'char' | 'int' | 'float'


def build_function_body(node):
    plist_node = child_named(node, "Parameter-list")
    slist_node = child_named(node, "Statement-list")
    params = build_parameter_list(plist_node) if plist_node is not None else []
    stmts = build_statement_list(slist_node) if slist_node is not None else []
    return params, stmts


def build_parameter_list(node):
    if not node.children:
        return []
    p_node = child_named(node, "Parameter")
    rest_node = child_named(node, "Parameter-list")
    params = [build_parameter(p_node)] if p_node else []
    if rest_node is not None:
        params += build_parameter_list(rest_node)
    return params


def build_parameter(node):
    finit = child_named(node, "Function-initial")
    t, n = build_function_initial(finit)
    return Param(n, t, line=node_line(finit))


# ------------------------------------------------------------- statements --
def build_statement_list(node):
    if not node.children:
        return []
    s_node = child_named(node, "Statement")
    rest_node = child_named(node, "Statement-list")
    stmts = [build_statement(s_node)] if s_node else []
    if rest_node is not None:
        stmts += build_statement_list(rest_node)
    return stmts


def build_statement(node):
    dispatch = (
        ("Declaration-stmt", build_declaration),
        ("Assign-stmt", build_assign),
        ("Conditional-stmt", build_conditional),
        ("Return-stmt", build_return),
    )
    for name, builder in dispatch:
        child = child_named(node, name)
        if child is not None:
            return builder(child)
    return None


def build_declaration(node):
    type_node = child_named(node, "Type-specifier")
    id_node = child_named(node, "ID")
    decl_id_node = child_named(node, "Declaration-Id")
    vtype = build_type_specifier(type_node)
    names = [terminal_text(id_node)]
    if decl_id_node is not None:
        names += build_declaration_id(decl_id_node)
    return Declaration(vtype, names, line=node_line(id_node))


def build_declaration_id(node):
    id_node = child_named(node, "ID")
    if id_node is None:
        return []  # matched ';' alternative
    rest_node = child_named(node, "Declaration-Id")
    names = [terminal_text(id_node)]
    if rest_node is not None:
        names += build_declaration_id(rest_node)
    return names


def build_assign(node):
    id_node = child_named(node, "ID")
    expr_node = child_named(node, "Expression")
    return Assign(terminal_text(id_node), build_expression(expr_node), line=node_line(id_node))


def build_return(node):
    rt_node = child_named(node, "Return-type")
    return Return(build_return_type(rt_node), line=node_line(rt_node))


def build_return_type(node):
    id_node = child_named(node, "ID")
    if id_node is not None:
        return Id(terminal_text(id_node), line=node_line(id_node))
    num_node = child_named(node, "NUMBER")
    if num_node is not None:
        return Num(terminal_text(num_node), line=node_line(num_node))
    let_node = child_named(node, "LETTER")
    if let_node is not None:
        return Letter(terminal_text(let_node), line=node_line(let_node))
    return None


# ---------------------------------------------------------- conditionals --
def build_conditional(node):
    cond_node = child_named(node, "Condition")
    body_node = child_named(node, "Statement-body")
    nest_node = child_named(node, "Conditional-nest")
    condition = build_condition(cond_node)
    then_body = build_statement_body(body_node)
    elifs, else_body = build_conditional_nest(nest_node) if nest_node is not None else ([], None)
    return If(condition, then_body, elifs, else_body, line=node_line(cond_node))


def build_statement_body(node):
    stmt_node = child_named(node, "Statement")
    if stmt_node is not None:
        return [build_statement(stmt_node)]
    slist_node = child_named(node, "Statement-list")
    return build_statement_list(slist_node) if slist_node is not None else []


def build_condition(node):
    id_node = child_named(node, "ID")
    relop_node = child_named(node, "Rel-op")
    expr_node = child_named(node, "Expression")
    compound_node = child_named(node, "Compound-condition")
    logop, rest = (None, None)
    if compound_node is not None:
        logop, rest = build_compound_condition(compound_node)
    return Condition(terminal_text(id_node), build_relop(relop_node),
                      build_expression(expr_node), logop, rest, line=node_line(id_node))


def build_compound_condition(node):
    if not node.children:
        return None, None
    logop_node = child_named(node, "Log-op")
    cond_node = child_named(node, "Condition")
    return build_logop(logop_node), build_condition(cond_node)


def build_relop(node):
    return node.children[0].name  # '<=' '>=' '==' '<' '>' '!='


def build_logop(node):
    return node.children[0].name  # '&&' '||'


def build_conditional_nest(node):
    if not node.children:
        return [], None
    cb_node = child_named(node, "Condition-body")
    return build_condition_body(cb_node)


def build_condition_body(node):
    elif_node = child_named(node, "Elif-stmt")
    if elif_node is not None:
        return build_elif(elif_node)
    else_node = child_named(node, "Else-stmt")
    return [], build_else(else_node) if else_node is not None else None


def build_elif(node):
    if not node.children:
        return [], None
    cond_node = child_named(node, "Condition")
    body_node = child_named(node, "Statement-body")
    nest_node = child_named(node, "Conditional-nest")
    entry = (build_condition(cond_node), build_statement_body(body_node))
    more_elifs, else_body = build_conditional_nest(nest_node) if nest_node is not None else ([], None)
    return [entry] + more_elifs, else_body


def build_else(node):
    body_node = child_named(node, "Statement-body")
    return build_statement_body(body_node) if body_node is not None else []


# ------------------------------------------------------------ expressions --
def build_expression(node):
    letter_node = child_named(node, "LETTER")
    if letter_node is not None:
        return Letter(terminal_text(letter_node), line=node_line(letter_node))
    term_node = child_named(node, "Term")
    top_node = child_named(node, "Term-op")
    left = build_term(term_node)
    return apply_term_op(left, top_node) if top_node is not None else left


def build_term(node):
    return build_factor(child_named(node, "Factor"))


def apply_term_op(left, node):
    if not node.children:
        return left  # EPSILON
    for op in ("+", "-"):
        op_node = child_named(node, op)
        if op_node is not None:
            right = build_expression(child_named(node, "Expression"))
            return BinOp(op, left, right)
    for op in ("*", "/"):
        op_node = child_named(node, op)
        if op_node is not None:
            right = build_factor(child_named(node, "Factor"))
            return BinOp(op, left, right)
    return left


def build_factor(node):
    id_node = child_named(node, "ID")
    if id_node is not None:
        return Id(terminal_text(id_node), line=node_line(id_node))
    num_node = child_named(node, "NUMBER")
    if num_node is not None:
        return Num(terminal_text(num_node), line=node_line(num_node))
    dec_node = child_named(node, "DECIMAL")
    if dec_node is not None:
        return Dec(terminal_text(dec_node), line=node_line(dec_node))
    paren_node = child_named(node, "(")
    if paren_node is not None:
        return build_expression(child_named(node, "Expression"))
    return None


# -------------------------------------------------------------- Main func --
def build_main(node):
    mfi = child_named(node, "Main-func-initial")
    fbody = child_named(node, "Function-body")
    type_node = child_named(mfi, "Type-specifier")
    ret_type = build_type_specifier(type_node)
    params, stmts = build_function_body(fbody)
    return Function("main", ret_type, params, stmts, is_main=True, line=node_line(mfi))
