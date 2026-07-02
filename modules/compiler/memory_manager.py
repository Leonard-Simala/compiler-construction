#from modules import symbolTableManager
from modules.symbolTableManager.symbolTableManager import SymbolTableManager
#from symbolTableManager import SymbolTableManager


class MemoryManager(object):
    ''' Manages shared information about memory locations '''

    @classmethod
    def init(cls):
        cls.static_base_ptr = 1000
        cls.temp_base_ptr   = 5000
        cls.stack_base_ptr  = 10008

        cls.static_offset   = 0
        cls.temp_offset     = 0

        cls.args_field_offset   = 4
        cls.locals_field_offset = 0
        cls.arrays_field_offset = 0
        cls.temps_field_offset  = 0

        cls.pb_index = 0  # program block index


    @classmethod
    def reset(cls):
        ''' call this when finished creating stack frame '''
        cls.args_field_offset  = 4
        cls.locals_field_offset = 0
        cls.array_field_offset = 0
        cls.temp_field_offset  = 0

    
    @classmethod
    def get_temp(cls):
        temp = cls.temp_base_ptr + cls.temp_offset
        cls.temp_offset += 4
        SymbolTableManager.temp_stack[-1] += 4
        return temp 


    @classmethod
    def get_static(cls, arity=1):
        temp = cls.static_base_ptr + cls.static_offset
        cls.static_offset += 4 * arity
        return temp


    @classmethod
    def get_param_offset(cls, arity=1):
        offset = cls.args_field_offset
        cls.args_field_offset += 4
        return offset
