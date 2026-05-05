# memory.py
storage = []             
next_free_address = 0    
_next_address = 1000
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def define(self, name, info):
        if name in self.symbols:
            raise NameError(f"錯誤：變數 '{name}' 在此作用域已宣告過！")
        self.symbols[name] = info
        
    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

def allocate_memory(size=1):
    global next_free_address
    addr = next_free_address
    _next_address += size
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
    if 0 <= address < len(storage):
        return storage[address]
    else:
        raise MemoryError(f"Segmentation Fault: 嘗試讀取無效位址 {address}")

def reset_memory():
    """徹底重置記憶體與位址計數器"""
    global next_free_address, storage
    next_free_address = 0
    storage.clear()