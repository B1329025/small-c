# memory.py

# --- 全域儲存空間 ---
macros = {}              # 存放 #define 等巨集
storage = []             # 實際模擬物理記憶體的陣列 (RAM)
next_free_address = 0    # 下一個可分配的起始位址

# --- 符號表類別 (Symbol Table) ---
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}     # 存放當前層的變數資訊 (位址、型別、狀態)
        self.parent = parent  # 指向父層的指標，形成作用域鏈

    def define(self, name, info):
        """在當前作用域定義變數"""
        if name in self.symbols:
            raise NameError(f"錯誤：變數 '{name}' 在此作用域已宣告過！")
        self.symbols[name] = info
        
    def lookup(self, name):
        """遞迴查找變數 (向上爬樓梯機制)"""
        # 1. 檢查自己這層
        if name in self.symbols:
            return self.symbols[name]
        # 2. 如果自己這層找不到，且有父層，就往上找
        if self.parent:
            return self.parent.lookup(name)
        # 3. 找遍了都沒有
        return None

# --- 記憶體管理函式 ---

def allocate_memory(size=1):
    """
    分配指定大小的空間。
    會同時回傳位址，並在物理儲存空間 (storage) 中預留位置。
    """
    global next_free_address
    addr = next_free_address
    
    # 自動擴充物理空間，預設填入 0 (模擬初始化)
    # 這樣 Parser 或 Evaluator 就不用自己手動 append 了
    for _ in range(size):
        storage.append(0)
        
    next_free_address += size
    return addr

def write(address, value):
    """安全的寫入函式：檢查是否越界"""
    if 0 <= address < len(storage):
        storage[address] = value
    else:
        raise MemoryError(f"Segmentation Fault: 嘗試寫入無效位址 {address}")

def read(address):
    """安全的讀取函式：檢查是否越界"""
    if 0 <= address < len(storage):
        return storage[address]
    else:
        raise MemoryError(f"Segmentation Fault: 嘗試讀取無效位址 {address}")

def reset_memory():
    """重置所有記憶體狀態 (測試時好用)"""
    global next_free_address, storage, macros
    next_free_address = 0
    storage = []
    macros = {}

def set_macro(name, value):
    """處理 #define 巨集"""
    macros[name] = value

def get_macro(name):
    """取得巨集數值"""
    return macros.get(name, None)
