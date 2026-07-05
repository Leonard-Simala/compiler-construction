class SymbolTableManager(object):

    _global_funcs = [{
        "lexim": "output",
        "scope": 0,
        "type": "void",
        "role": "function",
        "arity": 1,
        "params": ["int"]
    }]

    @classmethod
    def init(cls):
        cls.scope_stack = [0]
        cls.temp_stack = [0]
        cls.arg_list_stack = []
        cls.symbol_table = cls._global_funcs.copy()
        cls.declaration_flag = False
        cls.error_flag = False

    @classmethod
    def scope(cls):
        return len(cls.scope_stack) - 1

    # inserting new leximes to symbol table
    @classmethod
    def insert(cls, lexim):
        cls.symbol_table.append({"lexim" : lexim, "scope" : cls.scope()})

    # checking to avoid duplicate entries in symbol table
    @classmethod
    def _exists(cls, lexim, scope):
        for row in cls.symbol_table:
            if row["lexim"] == lexim and row["scope"] == scope:
                return True
        return False


    @classmethod
    def findrow(cls, value, attr="lexim"):
        for i in range(len(cls.symbol_table) - 1, -1, -1): 
            row = cls.symbol_table[i]
            if row[attr] == value:
                return row
        return None

    @classmethod
    def findrow_idx(cls, value, attr="lexim"):
        for i in range(len(cls.symbol_table) - 1, -1, -1): 
            row = cls.symbol_table[i]
            if row[attr] == value:
                return i
        return None
    
    # getting the length of the symbol table to get the id for the next symbol
    @classmethod
    def install_id(cls, lexim): 
        if not cls.declaration_flag:
            i = cls.findrow_idx(lexim)
            if i is not None:
                return i
        return len(cls.symbol_table)

    @classmethod
    def get_enclosing_fun(cls, level=1):
        try:
            return cls.symbol_table[cls.scope_stack[-level] - 1]
        except IndexError:
            return None

