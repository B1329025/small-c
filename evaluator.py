from nodes import *
import memory
class Evaluator:
    def __init__(self):
        self.functions = {}
        self.global_scope = memory.SymbolTable(parent=None)

    def reset_state(self):
        self.functions = {}
        self.global_scope = memory.SymbolTable(parent=None)
        memory.reset_memory() # 修正：必須清空物理記憶體[cite: 16]
    def execute_top_level(self, nodes):
        # 注意：這裡不呼叫 self.reset_state()，以便保留變數
        result = None
        for node in nodes:
            if isinstance(node, (FunctionDeclarationNode, VarDeclarationNode, ArrayDeclarationNode)):
                self.register_global(node) # 註冊全域宣告[cite: 18]
            else:
                # 直接執行陳述句 (如 printf)[cite: 18]
                result = self.evaluate(node, self.global_scope)
        return result

    def register_global(self, node):
        if isinstance(node, FunctionDeclarationNode):
            self.functions[node.name] = node
        elif isinstance(node, VarDeclarationNode):
            addr = memory.allocate_memory(1)
            val = self.evaluate(node.init_node, self.global_scope) if node.init_node else 0
            memory.write(addr, val)
            self.global_scope.define(node.var_name, {
                'address': addr, 'size': 1, 'type': node.var_type, 'initialized': True 
            })
        elif isinstance(node, ArrayDeclarationNode):
            # 全域陣列分配
            size = self.evaluate(node.size_node, self.global_scope)
            addr = memory.allocate_memory(size)
            self.global_scope.define(node.var_name, {
                'type': 'array', 'address': addr, 'size': size, 'initialized': False
            })

    def run_main(self, nodes):
        self.reset_state()
        for node in nodes:
            self.register_global(node)
        if 'main' not in self.functions:
            raise RuntimeError("錯誤：未定義 main() 函式")
        main_node = self.functions['main']
        main_scope = memory.SymbolTable(parent=self.global_scope)
        return self.evaluate(main_node.body, main_scope)
    def calculate_compound(self, current_val, rhs_val, op):
        if op == 'PA':      return current_val + rhs_val
        if op == 'TA':      return current_val * rhs_val
        if op == 'MA':      return current_val - rhs_val
        if op == 'DA':
            if rhs_val == 0: raise ZeroDivisionError("分母不可是零")
            return int(current_val / rhs_val)
        if op == 'MOD_A':   return current_val % rhs_val
        raise RuntimeError(f"未知的指定運算子: {op}")
    def evaluate(self,node,scope):
            if node is None:  
                return None
            if isinstance(node ,NumberNode):
                return node.value
            if isinstance(node, VarNode):
                info = scope.lookup(node.name)
                if not info: raise NameError(f"未定義: {node.name}")
                if info.get('type') == 'array': return info['address']
                return memory.read(info['address'])
            if isinstance(node, AssignNode):
                target_addr = None
                info = None
                if isinstance(node.left, UnaryOpNode) and node.left.op == 'DEREF':
                    target_addr = self.evaluate(node.left.operand, scope)
                elif isinstance(node.left, ArrayAccessNode):
                    info = scope.lookup(node.left.name)
                    if not info: raise NameError(f"未定義陣列 {node.left.name}")
                    idx = self.evaluate(node.left.index_node, scope)
                    target_addr = info['address'] + idx
                elif isinstance(node.left, VarNode):
                    info = scope.lookup(node.left.name)
                    if not info: raise NameError(f"未定義變數 {node.left.name}")
                    target_addr = info['address']

                rhs_val = self.evaluate(node.right, scope)
                
                # 處理字串賦值
                if info and info.get('type') == 'array' and isinstance(node.right, StringNode):
                    for i, c in enumerate(node.right.value):
                        memory.write(info['address'] + i, ord(c))
                    memory.write(info['address'] + len(node.right.value), 0)
                    info['initialized'] = True
                    return rhs_val

                final_val = rhs_val
                if node.op != 'assign':
                    cur = memory.read(target_addr)
                    final_val = self.calculate_compound(cur, rhs_val, node.op)
                
                memory.write(target_addr, final_val)
                if info: info['initialized'] = True
                return final_val
            if isinstance(node ,UnaryOpNode):
                if node.op == 'DEREF':
                    return memory.read(self.evaluate(node.operand, scope))
                if node.op == 'ADDRESS_OF':
                    return scope.lookup(node.operand.name)['address']
                if node.op =='NEGATIVE':
                    val =self.evaluate(node.operand,scope)
                    return -val
                if node.op =='BIT_NOT':
                    val =self.evaluate(node.operand,scope)
                    return ~val
                if node.op =='NOT':
                    val =self.evaluate(node.operand,scope)
                    return 1 if val==0 else 0
            if isinstance(node, IfNode):
                if self.evaluate(node.condition, scope):
                    return self.evaluate(node.then_block, scope)
                elif node.else_block:
                    return self.evaluate(node.else_block, scope)
                return None      
            if isinstance(node, BlockNode):
                res = None
                block_scope = memory.SymbolTable(parent=scope)
                for s in node.statements:
                    res = self.evaluate(s, block_scope)
                return res
            if isinstance(node, WhileNode):
                result=None
                while self.evaluate(node.condition, scope):
                    result=self.evaluate(node.then_block, scope)
                return result    
            if isinstance(node,ArrayAccessNode):
                info = scope.lookup(node.name)
                base_addr = info['address']
                size = info['size']
                index=self.evaluate(node.index_node, scope)
                if index<0 or index>=size:
                    raise RuntimeError(f"索引越界！陣列 {node.name} 長度為 {size}，但存取了索引 {index}")
                return memory.read(base_addr + index)
            
            if isinstance(node, PrintNode):
                # 1. 先計算所有參數的值
                arg_values = [self.evaluate(arg, scope) for arg in node.args]
                fmt = node.format_string
                result = ""
                arg_idx = 0
                i = 0
                while i < len(fmt):
                    if fmt[i] == '\\' and i + 1 < len(fmt) and fmt[i+1] == 'n':
                        result += "\n"  # 將原始字串中的 \ 和 n 轉換為真正的換行符
                        i += 2
                    elif fmt[i] == '%' and i + 1 < len(fmt):
                        specifier = fmt[i+1]
                        if specifier == '%': # 輸出百分比符號本身
                            result += "%"
                            i += 2
                            continue
                        
                        if arg_idx >= len(arg_values):
                            raise RuntimeError("printf 格式字串與參數數量不符")
                        val = arg_values[arg_idx]
                        arg_idx += 1
                        
                        if specifier == 'd': # 整數
                            result += str(int(val))
                        elif specifier == 'c': # 字元
                            result += chr(int(val))
                        elif specifier == 'x': # 十六進位
                            result += hex(int(val))[2:]
                        elif specifier == 's': # 字串 (假設 val 是記憶體位址)
                            addr = val
                            s_val = ""
                            # 模擬讀取直到遇到 \0
                            try:
                                while True:
                                    # 讀取位址內容
                                    char_code = memory.read(addr) 
                                    
                                    # 遇到結尾符 \0 則停止
                                    if char_code == 0: 
                                        break
                                    
                                    s_val += chr(char_code)
                                    addr += 1
                                    
                                    # 安全機制：防止無限迴圈（可選）
                                    if len(s_val) > 1000: 
                                        break
                            except Exception:
                                raise RuntimeError(f"Runtime error: 讀取字串時記憶體存取越界 (位址: {addr})")
                            result += s_val
                        else:
                            raise RuntimeError(f"printf 錯誤：不支援的佔位符 '%{specifier}'")
                        i += 2 # 跳過 % 和佔位符
                    else:
                        result += fmt[i]
                        i += 1
                if arg_idx < len(arg_values):
                    raise RuntimeError(f"printf 錯誤：提供的參數 ({len(arg_values)}) 多於格式字串所需的數量 ({arg_idx})")
                print(result, end='', flush=True)
                return None
            
            # 處理陣列宣告執行
            if isinstance(node, ArrayDeclarationNode):
                # 1. 計算大小
                size = self.evaluate(node.size_node, scope)
                # 2. 分配記憶體
                base_address = memory.allocate_memory(size)
                if node.init_node and isinstance(node.init_node, StringNode):
                    content = node.init_node.value
                    # 檢查空間是否足夠存放字串 + \0
                    if len(content) >= size:
                        raise IndexError(f"Runtime error: array size {size} is too small for string '{content}' with null terminator.")
                    # 寫入字元
                    for i in range(len(content)):
                        memory.write(base_address + i, ord(content[i]))  
                    # 強制補上結尾符 \0
                    memory.write(base_address + len(content), 0)

                scope.define(node.var_name, {
                    'type': 'array',
                    'element_type': node.var_type,
                    'address': base_address,
                    'size': size,
                    'initialized': True if node.init_node else False
                })
                return base_address

            # 處理一般變數宣告執行
            if isinstance(node, VarDeclarationNode):
                addr = memory.allocate_memory(1)
                val = 0
                if node.init_node:
                    val = self.evaluate(node.init_node, scope)
                    memory.write(addr, val)
                
                scope.define(node.var_name, {
                    'address': addr,
                    'size': 1,
                    'type': node.var_type,
                    'initialized': True 
                })
                return val
            if isinstance(node, StringNode):
                # 1. 在記憶體中分配空間 (字串長度 + 1 個 '\0' 結束符)
                base_address = memory.allocate_memory(len(node.value) + 1)
                # 2. 逐一寫入 ASCII 碼
                for i, char in enumerate(node.value):
                    memory.write(base_address + i, ord(char))
                memory.write(base_address + len(node.value), 0) # 寫入結束符 \0
                return base_address # 回傳字串的首位址
            if isinstance(node, ForNode):
                # 1. 建立執行期的獨立作用域 (parent 指向當前的 scope)
                for_scope = memory.SymbolTable(parent=scope)
                
                # 2. 執行初始化 (關鍵：傳入 for_runtime_scope)
                # 如果 node.init 是 int i = 0，i 就會被定義在 for_runtime_scope 裡
                if node.init:
                    self.evaluate(node.init, for_scope)
                
                last_result = None
                while True:
                    if node.condition:
                        if not self.evaluate(node.condition, for_scope): break
                    last_result = self.evaluate(node.body, for_scope)
                    if node.update: self.evaluate(node.update, for_scope)
                return last_result
            if isinstance(node, BinOpNode):
                # --- 邏輯運算：特殊處理（短路） ---
                if node.op == 'LOGICAL_AND':
                    left_val = self.evaluate(node.left, scope)
                    if left_val == 0:return 0  # 左邊為假，右邊連 evaluate 都不呼叫
                    return 1 if self.evaluate(node.right, scope) else 0

                if node.op == 'LOGICAL_OR':
                    left_val = self.evaluate(node.left, scope)
                    if left_val != 0: return 1  # 左邊為真，直接短路回傳真
                    return 1 if self.evaluate(node.right, scope) else 0
                
                left_val = self.evaluate(node.left, scope)
                right_val = self.evaluate(node.right, scope)
                if node.op == 'PLUS': return left_val + right_val
                if node.op == 'TIMES': return left_val * right_val
                if node.op == 'DIVIDE':
                    if right_val ==0: raise ZeroDivisionError("除以零錯誤")
                    return int(left_val / right_val)
                if node.op == 'MINUS': return left_val - right_val
                if node.op == 'MOD': 
                    if right_val ==0: raise ZeroDivisionError("除以零錯誤")
                    return left_val - (int(left_val / right_val) * right_val)
                if node.op == 'XOR': return left_val^right_val
                if node.op == 'OR': return left_val | right_val
                if node.op == 'rs': return left_val >> right_val
                if node.op == 'ls': return left_val << right_val
                if node.op == 'E': return 1 if left_val == right_val else 0
                if node.op == 'LE': return 1 if left_val <= right_val else 0
                if node.op == 'GE': return 1 if left_val >= right_val else 0
                if node.op == 'L': return 1 if left_val < right_val else 0
                if node.op == 'G': return 1 if left_val > right_val else 0
                if node.op == 'NE': return 1 if left_val != right_val else 0
                if node.op == 'BIT_AND':return left_val & right_val             
            raise RuntimeError(f"未知的節點類型：{type(node)}")