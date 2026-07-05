"""
=============================================================================
Module      : memoryManager.py
Description :
Author      : Leonard Simala
Date        : 2023-04-03
Version     : 1.0.0
=============================================================================
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
