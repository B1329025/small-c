# memory.py
storage = []             
next_free_address = 0    
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}  # 格式: {'var_name': {'address': 0, 'type': 'int', ...}}
        self.parent = parent # 指向上層作用域

    def define(self, name, info):
        if name in self.symbols:
            raise NameError(f"Runtime Error: 變數 '{name}' 已在此作用域宣告過")
        self.symbols[name] = info
        
    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

def allocate_memory(size=1):
    """
    根據需求大小分配連續空間，並回傳起始位址。
    """
    global next_free_address
    addr = next_free_address
    # 擴展儲存空間並初始化為 0
    for _ in range(size):
        storage.append(0)
    next_free_address += size
    return addr

def write(address, value):
    if 0 <= address < len(storage):
        storage[address] = value
    else:
        raise MemoryError(f"Segmentation Fault: 嘗試寫入無效位址 {address}")

def read(address):
    """從指定位址讀取數值[cite: 39]"""
    if 0 <= address < len(storage):
        return storage[address]
    else:
        raise MemoryError(f"Segmentation Fault: 嘗試讀取位址 {address}")

def reset_memory():
    global next_free_address, storage
    next_free_address = 0
    storage.clear()