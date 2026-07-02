char_to_col = {        # abbreviations in DFA
    "WHITESPACE" : 0,  # w
    "DIGIT"      : 1,  # d
    "LETTER"     : 2,  # l
    "'"          : 3,  # ' (for charcaters)
    "SYMBOL"     : 4,  # s
    # arithmetic operator symbols
    "+"          : 5,  # +
    "-"          : 6,  # - 
    # symbols used to create comments, newlines, floats, include statements, logical operators & relational operators
    "*"          : 7,  # *
    "="          : 8,  # =
    "/"          : 9,  # /
    "<"          : 10,  # <
    ">"          : 11,  # >
    "&"          : 12,  # &
    "|"          : 13,  # |
    "!"          : 14,  # !
    "\n"         : 15,  # \n
    "."          : 16,  # .
    "OTHER"      : 17,  # i # Anything else, only valid inside comment block    
}

token_dfa = (
    # Input LETTER types
    #   w     d       l    '     s     +     -     *     =     /     <     >     &     |     !     /n    .     i   
    #   0     1       2    3     4     5     6     7     8     9     10    11    12    13    14    15    16    17 
    (   1,      2,    8,   10,   14,   15,   17,   19,   22,   25,   31,   34,   37,   39,   41,   43, None,   44),  # State 0 (initital state)
    (   1,   None, None, None, None, None, None, None, None, None, None, None, None, None, None,    1, None, None),  # State 1 (WHITESPACE)
    (   3,      2,    4,    3,    3,    3,    3,    3,    3,    3,    3,    3,    3,    3,    3,    3,    5,    4),  # State 2 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None),  # State 3 (NUMBER)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None),  # State 4 (illegal number)
    (  45,      6,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45,   45),  # State 5 
    (   7,      6,    7,    7,    7,    7,    7,    7,    7,    7,    7,    7,    7,    7,    7,    7,    7,   45),  # State 6 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 7 (FLOAT)   
    (    9,    8,    8,    9,     9,    9,    9,    9,    9,    9,    9,    9,    9,    9,    9,    9,    9,   44),  # State 8 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 9 (IDENTIFIER/KEYWORD)
    (  11,     11,   11,   11,   11,   11,   11,   11,   11,   11,   11,   11,   11,   11,   11,   11,    11,   11), # State 10 
    (  46,     46,   46,   12,   46,   46,   46,   46,   46,   46,   46,   46,   46,   46,   46,   46,    46,   44), # State 11 
    (  13,     13,   13,   13,   13,   13,   13,   13,   13,   13,   13,   13,   13,   13,   13,   13,    13,   44), # State 12
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 13 (LETTER) 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 14 (SYMBOL)
    (  16,     16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,   16,    16,   44), # State 15 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 16 (ADD)
    (  18,     18,   18,   18,   18,   18,   18,   18,   18,   18,   18,   18,   18,   18,   18,   18,    18,   44), # State 17 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 18 (SUB)
    (  20,     20,   20,   20,   20,   20,   20,   20,   20,   21,   20,   20,   20,   20,   20,   20,    20,   44), # State 19 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 20 (MULT)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 21 (unmatched */)
    (  23,     23,   23,   23,   23,   23,   23,   23,   24,   23,   23,   23,   23,   23,   23,   23,    23,   44), # State 22 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 23 (ASSIGN)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 24 (EQUALTO)
    (  30,     30,   30,   30,   30,   30,   30,   26,   30,   29,   30,   30,   30,   30,   30,   30,    30,   44), # State 25   
    (  26,     26,   26,   26,   26,   26,   26,   27,   26,   26,   26,   26,   26,   26,   26,   26,    26,   26), # State 26 
    (  47,     47,   47,   47,   47,   47,   47,   27,   47,   28,   47,   47,   47,   47,   47,   47,    47,   47), # State 27 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 28 (COMMENT)
    (  29,     29,   29,   29,   29,   29,   29,   29,   29,   29,   29,   29,   29,   29,   29,   28,    29,   29), # State 29
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 30 (DIV)
    (  32,     32,   32,   32,   32,   32,   32,   32,   33,   32,   32,   32,   32,   32,   32,   32,    32,   44), # State 31
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 32 (LESSTHAN)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 33 (LESSEQUAL)
    (  35,     35,   35,   35,   35,   35,   35,   35,   36,   35,   35,   35,   35,   35,   35,   35,    35,   44), # State 34 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 35  (GREATERTHAN)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 36  (GREATEREQUAL)
    (  44,     44,   44,   44,   44,   44,   44,   44,   44,   44,   44,   44,   38,   44,   44,   44,    44,   44), # State 37 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 38 (AND)
    (  44,     44,   44,   44,   44,   44,   44,   44,   44,   44,   44,   44,   44,   40,   44,   44,    44,   44), # State 39 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 40 (OR)
    (  44,     44,   44,   44,   44,   44,   44,   44,   42,   44,   44,   44,   44,   44,   44,   44,    44,   44), # State 41 
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 42 (NOTEQUAL)
    (  43,   None, None, None, None, None, None, None, None, None, None, None, None, None, None,   43,  None, None), # State 43 (WHITESPACE)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 44 (invalid input)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 45 (illegal float)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 46 (illegal LETTER)
    (None,   None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,  None, None), # State 47 (illegal comment)
)

state_to_token = {
    1  : "WHITESPACE",
    3  : "NUMBER",
    7  : "DECIMAL",
    9  : "ID_OR_KEYWORD",
    13 : "LETTER",
    14 : "SYMBOL",
    16 : "ADD",
    18 : "SUB",
    20 : "MULT",
    23 : "ASSIGN",
    24 : "EQUAL_TO",
    28 : "COMMENT",
    30 : "DIV",
    32 : "LESS_THAN",
    33 : "LESS_EQUAL",
    35 : "GREATER_THAN",
    36 : "GREATER_EQUAL",
    38 : "AND",
    40 : "OR",
    42 : "NOT_EQUAL",
    43 : "WHITESPACE"
}

state_to_error_message = {
     4  : "Illegal integer",
     21  : "Unmatched */",
     44 : "Invalid input",
     45 : "Illegal float",
     46 : "Illegal LETTER",
     47 : "Illegal comment"
}

F = {1,3,7,9,13,14,16,18,20,23,24,28,30,32,33,35,36,38,40,42,43}   # all accepting states
Fstar = {3,7,9,16,18,20,23,30}  # accepting states that require the last character to be returned to the input stream
unclosed_comment_states = {26,27,29}
whitespaces = {' ', '\r', '\t', '\v', '\f'} # \n excluded as it has special meaning in one line comments