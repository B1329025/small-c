# memory.py
storage = []             
next_free_address = 0    
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}  # 格式: {'var_name': {'address': 0, 'type': 'int', ...}}
        self.functions = {}
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
    # ── 函式 API────────────────
    def define_function(self, name, node):
        """註冊一個使用者定義函式。不允許在同一個環境重複定義。"""
        if name in self.functions:
            raise NameError(f"Runtime Error: 函式 '{name}' 已重複定義")
        self.functions[name] = node

    def lookup_function(self, name):
        """尋找函式。因為 C 語言不支援巢狀函式定義，通常由全域符號表來查找。"""
        # 優先在當前作用域找
        if name in self.functions:
            return self.functions[name]
        # 如果當前不是全域（例如在某個函式區塊內），往上層（父級）追溯直到全域
        if self.parent:
            return self.parent.lookup_function(name)
        return None

    def get_all_functions(self):
        """回傳當前符號表中的所有自定義函式（通常用於全域）"""
        return self.functions

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
    """從指定位址讀取數值"""
    if 0 <= address < len(storage):
        return storage[address]
    else:
        raise MemoryError(f"Segmentation Fault: 嘗試讀取位址 {address}")

def reset_memory():
    global next_free_address, storage
    next_free_address = 0
    storage.clear()