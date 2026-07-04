"""
=============================================================================
Module      : parser.py
Description : Syntax Analyser for the compiler pipeline.
              Generates the parse tree
Author      : Leonard Simala
Date        : 2023-04-03
Version     : 1.0.0
=============================================================================
"""
import os
from anytree import Node, RenderTree, PreOrderIter
from modules.symbolTableManager.symbolTableManager import SymbolTableManager
from modules.scanner.scanner import Scanner
from modules.parserTable.parseTable import productions
from modules.parserTable.parseTable import terminal_to_col
from modules.parserTable.parseTable import non_terminal_to_row
from modules.parserTable.parseTable import parsing_table

# importing the file containing the code
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
class Parser(object):

    ''' Syntax analyzer class that parses the token stream from the scanner
    given a parse tree starting with input string
    '''
    # used to check whether the specified path is an absolute path 
    def __init__(self, input_file):
        if not os.path.isabs(input_file):
            input_file = os.path.join(script_dir, input_file)

        # initialising the Parser's attributes      
        self.scanner = Scanner(input_file)
        self._syntax_errors = []
        self.root = Node("Program") # The start symbol root of the tree
        self.parse_tree = self.root
        self.stack = [Node("$"), self.root]
        
        self.parse_tree_file = os.path.join(script_dir, "outputs", "parseTree.txt")
        self.syntax_error_file = os.path.join(script_dir, "errors", "syntaxErrors.txt")

    # getter for for sysntax errors
    @property    
    def syntax_errors(self):
        syntax_errors = []
        if self._syntax_errors:
            for lineno, error in self._syntax_errors:
                syntax_errors.append(f"#{lineno} : Syntax Error! {error}\n")
        else:
            syntax_errors.append("There is no syntax error.\n")
        return "".join(syntax_errors)

    # saving the parse tree 
    def save_parse_tree(self):
        with open(self.parse_tree_file, "w", encoding="utf-8") as f:
            for pre, _, node in RenderTree(self.parse_tree):
                if hasattr(node, "token"):
                    f.write(f"{pre}{node.token}\n")
                else:
                    f.write(f"{pre}{node.name}\n")

    #saving the (txt) file 
    def save_syntax_errors(self):
        with open(self.syntax_error_file, "w") as f:
            f.write(self.syntax_errors)

    # Removes node from the parse tree
    def _remove_node(self, node):
        try:
            parent = list(node.iter_path_reverse())[1]
            parent.children = [c for c in parent.children if c != node]
        except IndexError:
            pass

    def _clean_up_tree(self):
        # remove non terminals and unmet terminals from leaf nodes 
        remove_nodes = []
        for node in PreOrderIter(self.parse_tree):
            if not node.children and not hasattr(node, "token") and node.name != "EPSILON":
                remove_nodes.append(node)
        
        for node in remove_nodes:
            self._remove_node(node)
    

    def parse(self):
        clean_up_needed = False
        token = self.scanner.get_next_token()
        new_nodes = []
        while True:
            token_type, a = token
            a = a.strip() if isinstance(a, str) else a #Safe strip
            if token_type in ("ID", "NUMBER", "DECIMAL", "LETTER"):   # parser won't understand the lexim input in this case
                a = token_type

            current_node = self.stack[-1]     # check the top of the stack
            X = current_node.name

            if X in terminal_to_col.keys():   # X is a terminal
                if X == a:
                    if X == "$":
                        break
                    self.stack[-1].token = self.scanner.token_to_str(token)
                    self.stack.pop()
                    token = self.scanner.get_next_token()
                else:
                    SymbolTableManager.error_flag = True
                    if X == "$":
                        # parse stack unexpectedly exhausted
                        # self._clean_up_tree()
                        break
                    self._syntax_errors.append((self.scanner.line_number, f'Missing "{X}"'))
                    self.stack.pop()
                    clean_up_needed = True
            else: 
                # X is non-terminal
                # look up parsing table which production to use
                col = terminal_to_col[a]
                row = non_terminal_to_row[X]
                prod_idx = parsing_table[row][col]
                rhs = productions[prod_idx]

                if "SYNCH" in rhs:
                    SymbolTableManager.error_flag = True
                    if a == "$":
                        self._syntax_errors.append((self.scanner.line_number, "Unexpected EndOfFile"))

                        # self._clean_up_tree()
                        clean_up_needed = True
                        break
                    #missing_construct = non_terminal_to_missing_construct[X]
                    ##self._syntax_errors.append((self.scanner.line_number, f'Missing "{missing_construct}"'))
                    self._remove_node(current_node)
                    self.stack.pop()
                elif "EMPTY" in rhs:
                    SymbolTableManager.error_flag = True
                    self._syntax_errors.append((self.scanner.line_number, f'Illegal "{a}"'))
                    token = self.scanner.get_next_token()
                else:
                    self.stack.pop()
                    for symbol in rhs:
                        if not symbol.startswith("#"):
                            new_nodes.append(Node(symbol, parent=current_node))
                        else:
                            new_nodes.append(Node(symbol))

                    for node in reversed(new_nodes):
                        if node.name != "EPSILON":
                            self.stack.append(node)

                print(f"{X} -> {' '.join(rhs)}")  # prints out the productions used
                new_nodes = []

'''def main(input_path):
    import time
    import os
    from modules.intermediateCode.threeAdressCodes import TACGenerator
    from modules.memory.memoryManager import MemoryManager

    SymbolTableManager.init()

    # ── Parsing
    parser = Parser(input_path)
    start = time.time()
    parser.parse()
    stop = time.time() - start
    print(f"Parsing took {stop:.6f}s Check the parseTree.txt file in The outputs Folder")

    # Save parser outputs
    parser.save_parse_tree()
    parser.save_syntax_errors()
    parser.scanner.save_lexical_errors()
    parser.scanner.save_symbol_table()
    parser.scanner.save_tokens()

    # ── Memory Manager
    memory = MemoryManager()
    for row in SymbolTableManager.symbol_table:
        if "type" in row:
            memory.allocate(row["lexim"], row["type"])

    # ── TAC Generation
    tac_output = os.path.join(script_dir, "outputs", "threeAdressCodes.txt")
    tac = TACGenerator(parser.parse_tree, memory)
    tac.generate()
    tac.save(tac_output)'''

    '''# Test if Three Address codes are being printed.
    print("\n--- Three Address Code ---")
    for line in tac.code:
        print(line)'''

def main(input_path):
    import time
    from modules.semanticAnalysis.astBuilder import build_program
    from modules.semanticAnalysis.semanticAnalyser import SemanticAnalyzer
    from modules.intermediateCode.threeAdressCodes import TACGenerator
    SymbolTableManager.init()
    parser = Parser(input_path)
    start = time.time()
    parser.parse()
    stop = time.time() - start

    print(f"Parsing took {stop:.6f} s")
    parser.save_parse_tree()
    parser.save_syntax_errors()
    parser.scanner.save_lexical_errors()
    parser.scanner.save_symbol_table()
    parser.scanner.save_tokens()

    if SymbolTableManager.error_flag:
        print("Skipping semantic analysis / codegen due to syntax errors.")
        return

    # --- NEW: AST -> semantic analysis -> TAC ---------------------------
    program = build_program(parser.parse_tree)

    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)
    with open("outputs/semantic_errors.txt", "w") as f:
        f.write(analyzer.error_report)
    print(analyzer.error_report)

    if not analyzer.errors:
        tac = TACGenerator()
        tac.generate(program)
        with open("outputs/tac.txt", "w") as f:
            f.write(tac.pretty())
        print(tac.pretty())

    
if __name__ == "__main__":
    input_path = os.path.join(script_dir, "inputs/marks.c")
    main(input_path)
