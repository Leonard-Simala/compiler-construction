# modules/semantic/semantic_analyser.py

from anytree import PreOrderIter
from modules.symbolTableManager.symbolTableManager import SymbolTableManager

class SemanticAnalyser:
    def __init__(self, parse_tree):
        self.parse_tree = parse_tree
        self.errors = []

    def analyse(self):
        for node in PreOrderIter(self.parse_tree):
            self.check_node(node)

    def check_node(self, node):
        if node.name == "Declaration":
            self._check_declaration(node)
        elif node.name == "Assignment":
            self._check_assignment(node)
        elif node.name == "FunctionCall":
            self._check_function_call(node)

    def _check_declaration(self, node):

        # Check for duplicate in same scope
        children = list(node.children)
        var_name = children[1].name  # e.g int x → x is index 1
        if SymbolTableManager.findrow(var_name):
            self.errors.append(f"Error: '{var_name}' already declared in this scope")

    def _check_assignment(self, node):
        children = list(node.children)
        var_name = children[0].name

        # Check variable was declared
        if not SymbolTableManager.findrow(var_name):
            self.errors.append(f"Error: '{var_name}' used before declaration")