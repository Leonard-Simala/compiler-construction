"""
Memory Manager.

Responsible for storage layout: assigning each declared variable a byte
`offset` within its enclosing function's activation record, and computing
each function's total frame size (`Function.frame_size`, set by the
Semantic Analyzer after it finishes walking a function body).

Layout convention used here (adjust freely to match a codegen target you
have in mind):
    [ params ... | locals ... | temporaries (assigned later by TAC gen) ]
    offsets grow upward from 0 at the start of the frame.

Scoping: nested blocks (if/else bodies) share the *same* growing offset
counter as their enclosing function -- i.e. we don't reuse space between
sibling blocks. That's the simple/safe choice; if you later want block-local
reuse (declare a temp in an `if`, reclaim its space once the block ends),
`exit_block_scope()` is the place to add that.
"""


class MemoryManager:
    TYPE_SIZES = {"int": 4, "char": 1, "float": 4, "void": 0}

    _offset_stack = []   # top = current running offset for the active function/block
    _max_stack = []       # top = high-water mark for the active *function* (frame size)

    @classmethod
    def reset(cls):
        cls._offset_stack = []
        cls._max_stack = []

    # ---- function-level frame ------------------------------------------
    @classmethod
    def enter_function_scope(cls):
        cls._offset_stack.append(0)
        cls._max_stack.append(0)

    @classmethod
    def exit_function_scope(cls):
        cls._offset_stack.pop()
        return cls._max_stack.pop()   # -> frame_size for the function just finished

    # ---- nested block (if/else bodies) ----------------------------------
    @classmethod
    def enter_block_scope(cls):
        cls._offset_stack.append(cls._offset_stack[-1])

    @classmethod
    def exit_block_scope(cls):
        cls._offset_stack.pop()

    # ---- allocation -------------------------------------------------------
    @classmethod
    def allocate(cls, size):
        """Reserve `size` bytes in the current frame; return the assigned offset."""
        offset = cls._offset_stack[-1]
        cls._offset_stack[-1] += size
        if cls._offset_stack[-1] > cls._max_stack[-1]:
            cls._max_stack[-1] = cls._offset_stack[-1]
        return offset

    @classmethod
    def size_of(cls, type_name):
        return cls.TYPE_SIZES.get(type_name, 4)
