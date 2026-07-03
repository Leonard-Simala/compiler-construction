import os

from modules import symbolTableManager
from modules.symbolTableManager.symbolTableManager import SymbolTableManager

from modules.token_dfa.token_dfa import char_to_col
#from modules.symbolTableManager.symbolTableManager import SymbolTableManager
from modules.token_dfa.token_dfa import state_to_token
from modules.token_dfa.token_dfa import state_to_error_message
from modules.token_dfa.token_dfa import unclosed_comment_states
from modules.token_dfa.token_dfa import whitespaces
from modules.token_dfa.token_dfa import token_dfa
from modules.token_dfa.token_dfa import F
from modules.token_dfa.token_dfa import Fstar

script_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))


class Scanner(object):

    ''' Lexical analyzer class that tokenizes input C files
    according to our mini grammar'''

    def __init__(self, input_file,
                 chunk_size=8192,   # initialising a large chunk size for faster processing
                 max_state_size=float("inf")    # initialised to infinity
                 ):

        # making sure that the input file path is not empty
        assert chunk_size >= 16, "Minimum supported chunk size is 16!"
        if not os.path.isabs(input_file):
            input_file = os.path.join(script_dir, input_file)

        # initialising the scanner's attributes
        self.input_file = input_file
        self.line_number = 1
        self.first_line = 1
        self._lexical_errors = []
        self.tokens = {}
        self.tokens[self.line_number] = []      # access tokens by line number
        self.max_state_size = max_state_size    # how many lines of tokens we want to keep in memory (default: unlimited)

        self.tokens_file = os.path.join(script_dir, "outputs", "tokens.txt")
        self.symbol_file = os.path.join(
            script_dir, "outputs", "symbolTable.txt")
        self.errors_file = os.path.join(
            script_dir, "errors", "lexicalErrors.txt")

        self.chunk_size = chunk_size
        self.file_pointer = 0
        self.max_unclosed_comment_size = 15
        self.input = ""
        self.read_input()

        # lexical specification
        self.letters = {chr(i) for i in range(65, 91)} | {chr(i) for i in range(97, 123)}
        self.digits = {str(i) for i in range(0, 10)}
        self._symbols = {',', ';', '(', ')', '{', '}'}
        self.symbols = self._symbols | {'*', '/', '<', '>', '=', '&', '|', '!'}
        keywords = [
            "if",           # 0
            "else",         # 1
            "void",         # 2
            "int",          # 3
            "char",         # 4
            "float",        # 5
            "else if",      # 6
            "main",         # 7
            "while",        # 8
            "return",       # 9
        ]
        self.identifiers = keywords
        self.keywords = set(keywords)

    # ------ error handling functions ------

    # appends errors to lexical_errors array
    @property
    def lexical_errors(self):
        lexical_errors = []
        if self._lexical_errors:
            for lineno, lexim, error in self._lexical_errors:
                lexical_errors.append(
                    f"#{lineno} : Lexical Error! '{lexim}' rejected, reason: {error}.\n")
        else:
            lexical_errors.append("There is no lexical errors.\n")
        return "".join(lexical_errors)

    # writes contents of lexical_errors array to errors.txt
    def save_lexical_errors(self):
        if self.max_state_size > 0:
            with open(self.errors_file, "w") as f:
                f.write(self.lexical_errors)

    # ------ symbol table updating functions ------

    # assigns an id number to symbols in the symbol table

    def id_to_lexim(self, token_id):
        return symbolTableManager.symbolTableManager.SymbolTableManager.symbol_table[token_id]['lexim']

    def token_to_str(self, token):  # updates the symbol table with identifiers and keywords only
        if token[0] == "ID":
            return f"({token[0]}, {self.id_to_lexim(token[1])})"
        else:
            return "({}, {})".format(*token)

    # opens and reads file in binary
    def read_input(self):
        with open(self.input_file, "rb") as f:
            f.seek(self.file_pointer)
            chunk = f.read(self.chunk_size)
        if not chunk:  # making sure that the input file is not empty
            raise EOFError
        self.input += chunk.decode()
        self.file_pointer += self.chunk_size

    # matches input file lexemes to their token types defined in dfa
    def _resolve_dfa_table_column(self, input_char):
        if input_char in whitespaces:
            return char_to_col["WHITESPACE"]
        if input_char in self.letters:
            return char_to_col["LETTER"]
        if input_char in self.digits:
            return char_to_col["DIGIT"]
        if input_char in self._symbols:
            return char_to_col["SYMBOL"]
        try:
            return char_to_col[input_char]
        except KeyError:
            return char_to_col["OTHER"]

    # write identifiers to symbol_table.txt
    def save_symbol_table(self):
        with open(self.symbol_file, "w") as f:
            for i, symbol in enumerate(self.identifiers):
                f.write(f"{i+1}.\t{symbol}\n")

    # write tokens to tokens.txt
    def save_tokens(self):
        if self.max_state_size > 0:
            with open(self.tokens_file, "w") as f:
                for lineno, tokens in self.tokens.items():
                    if tokens:
                        f.write(
                            f"{lineno}.\t{' '.join([f'({t}, {l})' for t, l in tokens])}\n")

    # move to the next line of input file
    def _switch_line(self, num_lines):
        if num_lines > 0:
            for i in range(num_lines):
                self.tokens[self.line_number + i + 1] = []
            self.line_number += num_lines
            # remove leading whitespace from next line
            # (expect newlines as we need them for line number calculations)
            self.input = self.input.lstrip(" ").lstrip("\t")

    # attach an id to a symbol and append it to the symbol table
    def update_symbol_table(self, lexim):
        symbol_id = symbolTableManager.symbolTableManager.SymbolTableManager.install_id(lexim)
        if symbol_id == len(symbolTableManager.symbolTableManager.SymbolTableManager.symbol_table):
            symbolTableManager.symbolTableManager.SymbolTableManager.insert(lexim)
        return symbol_id

    # ------ tokenization function ------

    def get_next_token(self):
        save_state = None
        error_occurred = False
        input_ended = False
        s = 0  # initial state

        # if we're done reading a line of tokens, pop the line (saved in var first_line) and move to next line
        if len(self.tokens.keys()) > self.max_state_size:
            self.tokens.pop(self.first_line, None)
            self.first_line += 1

        # if we're done reading a line of errors, pop the error message from _lexical_errors
        if len(self._lexical_errors) > self.max_state_size:
            self._lexical_errors.pop(0)

        while True:  # Loop until we find valid token
            if not self.input or input_ended:   # if we're at the end of the file
                try:
                    self.read_input()
                except EOFError:
                    # error handling for unclosed comments
                    if s in unclosed_comment_states:
                        mucs = self.max_unclosed_comment_size
                        err_token = self.input[:mucs]
                        if len(self.input) > len(err_token):
                            err_token = err_token + " ..."
                        symbolTableManager.symbolTableManager.SymbolTableManager.error_flag = True
                        self._lexical_errors.append(
                            (self.line_number, err_token, "unclosed comment"))
                    self.line_number += self.input.count("\n")
                    self.input = ""
                    return ("EOF","$")

            token_candidates = []
            error_occurred = False
            input_ended = False

            s = 0 if save_state is None else save_state
            save_state = None

            # traverse the dfa as long as we can with the remaining input
            for i in range(len(self.input) + 1):
                try:
                    a = self.input[i]
                except IndexError:
                    a = self.input[-1]
                col = self._resolve_dfa_table_column(a)
                next_s = token_dfa[s][col]

                if s in state_to_error_message:  # are we in an error state?
                    if s == 22: # this is a lookahead error state (invalid comment)
                        i -= 1
                    lexim, error = self.input[:i], state_to_error_message[s]
                    if self.max_state_size > 0:
                        symbolTableManager.symbolTableManager.SymbolTableManager.error_flag = True
                        self._lexical_errors.append(
                            (self.line_number, lexim, error))
                    else:
                        print(
                            f"Lexical Error in line {self.line_number}: {error} '{lexim}'")
                    # skip invalid token (panic mode)
                    self.input = self.input[i:]
                    error_occurred = True
                    break

                if s in F:  # are we in an accepting state?
                    if s in Fstar:
                        token_candidates.append((s, self.input[:i-1]))
                    else:
                        token_candidates.append((s, self.input[:i]))

                if next_s is None:  # can we continue traversing dfa?
                    break
                elif i >= len(self.input):  # do we have enough input to do so?
                    # this only occurs for large files or small chunk size
                    if next_s not in F:
                        save_state = next_s
                    input_ended = True
                    break

                s = next_s

            if error_occurred or input_ended:
                continue

            if token_candidates:
                max_token = token_candidates[-1]  # pick maximal munch
                state, lexim = max_token
                self.input = self.input[len(lexim):]  # advance in the input
                token = state_to_token[state]

                if token == "WHITESPACE" or token == "COMMENT":  # these will not be returned
                    # update line number etc
                    self._switch_line(lexim.count("\n"))
                    continue  # proceed to next token

                if token == "ID_OR_KEYWORD":  # distinguish between ids and keywords
                    token = "KEYWORD" if lexim in self.keywords else "ID"

                if self.max_state_size > 0:
                    self.tokens[self.line_number].append(
                        (token, lexim))  # save tokens later for printing

                if token == "ID":
                    if lexim not in self.identifiers:
                        self.identifiers.append(lexim)
                    lexim = self.update_symbol_table(lexim)

                return (token, lexim)
            else:   # if line is outside defined token and error scope
                print(
                    f"[Panic Mode] Dropping '{self.input[:1]}' from line {self.line_number}")
                self.input = self.input[1:]


def main(input_path):
    import time
    scanner = Scanner(input_path)
    start = time.time()
    token = scanner.get_next_token()
    while token[0] != "EOF":
        token = scanner.get_next_token()
    stop = time.time() - start
    print(f"Scanning took {stop:.6f} s Check the Tokens.txt file in The outputs Folder")
    scanner.save_symbol_table()
    scanner.save_lexical_errors()
    scanner.save_tokens()

if __name__ == "__main__":
    symbolTableManager.symbolTableManager.SymbolTableManager.init()
    input_path = os.path.join(script_dir, "inputs/void.c")
    main(input_path)
