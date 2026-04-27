macros = {}
storage = []
next_free_address = 0
class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}       # 存放當前層的變數
        self.parent = parent    # 指向父層的指標

    def define(self, name, info):
        # 永遠定義在當前層，不需要往上找，因為宣告不能跨層
        if name in self.symbols:
            raise NameError(f"變數 '{name}' 已宣告過此變數名稱！")
        self.symbols[name] = info
        
    def lookup(self, name):
        # 1. 檢查自己
        if name in self.symbols:
            return self.symbols[name]
        # 2. 如果有父層，請父層幫忙找
        if self.parent:
            return self.parent.lookup(name)
        # 3. 真的沒人有
        return None
def allocate_memory(size=1):
    global next_free_address
    addr = next_free_address
    next_free_address += size
    return addr
global_scope = SymbolTable()