# modules/memory/memory_manager.py

class MemoryManager:
    BASE_ADDRESS = 100  # starting memory address

    def __init__(self):
        self.address_map = {}   # var_name → address
        self.current_offset = self.BASE_ADDRESS
        self.type_sizes = {
            "int": 4,
            "float": 8,
            "char": 1,
            "void": 0
        }

    def allocate(self, var_name, var_type):
        size = self.type_sizes.get(var_type, 4)
        self.address_map[var_name] = self.current_offset
        self.current_offset += size
        return self.address_map[var_name]

    def get_address(self, var_name):
        return self.address_map.get(var_name, None)

    def allocate_temp(self, temp_name, var_type="int"):
        return self.allocate(temp_name, var_type)

    def display(self):
        print("\n--- Memory Map ---")
        for var, addr in self.address_map.items():
            print(f"  {var} → address {addr}")