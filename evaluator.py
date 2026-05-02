from nodes import *
import memory
class Evaluator:
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
                if info is None:
                    raise NameError(f"變數 '{node.name}' 尚未宣告過！")
                if not info.get('initialized' ,True):
                    raise RuntimeError(f"變數 '{node.name}' 未初始化")
                if info.get('type') == 'array':
                    return info['address']
                return memory.read(info['address'])
            if isinstance(node, AssignNode):
                # 如果左邊是 *p (指標解引用)
                if isinstance(node.left, UnaryOpNode) and node.left.op == 'DEREF':
                    target_addr = self.evaluate(node.left.operand, scope)
                    rhs_val = self.evaluate(node.right, scope)
                    if node.op != 'assign':
                        old_val = memory.read(target_addr)
                        rhs_val = self.calculate_compound(old_val, rhs_val, node.op)
                    memory.write(target_addr, rhs_val)
                    return rhs_val
                if isinstance(node.left, ArrayAccessNode):
                    info = scope.lookup(node.left.name)
                    if info is None:
                        raise NameError(f"陣列 '{node.left.name}' 尚未宣告過！")
                    
                    index = self.evaluate(node.left.index_node, scope)
                    if index < 0 or index >= info['size']:
                        raise IndexError(f"索引 {index} 越界 (大小: {info['size']})")
                    
                    target_addr = info['address'] + index
                    rhs_val = self.evaluate(node.right, scope)
                    
                    final_val = self.calculate_compound(memory.read(target_addr), rhs_val, node.op) if node.op != 'assign' else rhs_val
                    memory.write(target_addr, final_val)
                    return final_val

                var_name = node.left.name if isinstance(node.left, VarNode) else node.left
                info = scope.lookup(var_name)
                if info is None:
                    raise NameError(f"變數 '{var_name}' 尚未宣告過！")
                
                # 2. 計算右值 (R-value)
                # 統一使用 node.right 而非 node.expression_node
                rhs_val = self.evaluate(node.right, scope)
                
                # 3. 處理陣列的字串賦值 (例如 char s[10]; s = "hello";)
                if info.get('type') == 'array' and isinstance(node.right, StringNode):
                    if node.op != 'assign': # 複合指定如 += 不支援字串
                        raise RuntimeError(f"陣列不支援 '{node.op}' 運算")
                    
                    base_addr = info['address']
                    raw_str = node.right.value # 使用 node.right
                    if len(raw_str) >= info['size']:
                        raise IndexError(f"Runtime error: string too long for array (size {info['size']})")
                    # 逐字元寫入記憶體
                    for i, char in enumerate(raw_str):
                        memory.write(base_addr + i, ord(char))
                    memory.write(base_addr + len(raw_str), 0) # 補上結束符號 \0
                    
                    info['initialized'] = True
                    return rhs_val     
                if node.op == 'assign':
                    final_val = rhs_val
                else:
                    current_val = memory.read(info['address'])
                    if node.op == 'PA':      final_val = current_val + rhs_val   
                    elif node.op == 'TA':    final_val = current_val * rhs_val   
                    elif node.op == 'MA':    final_val = current_val - rhs_val   
                    elif node.op == 'DA':   
                        if rhs_val == 0: raise ZeroDivisionError("分母不可是零")
                        final_val = int(current_val / rhs_val)
                    elif node.op == 'MOD_A': final_val = current_val % rhs_val   
                    else:
                        raise RuntimeError(f"未知的指定運算子: {node.op}")
                
                # 5. 將結果寫回記憶體[cite: 7]
                if info.get('type') != 'array':
                    memory.write(info['address'], final_val)
                
                info['initialized'] = True
                return final_val
            if isinstance(node ,UnaryOpNode):
                if node.op =='DEREF':
                    address = self.evaluate(node.operand, scope)
                    return memory.read(address)
                elif node.op =='ADDRESS_OF':
                    info =scope.lookup(node.operand.name)
                    return info['address']
                elif node.op =='NEGATIVE':
                    val =self.evaluate(node.operand,scope)
                    return -val
                elif node.op =='BIT_NOT':
                    val =self.evaluate(node.operand,scope)
                    return ~val
                elif node.op =='NOT':
                    val =self.evaluate(node.operand,scope)
                    return 1 if val==0 else 0
            if isinstance(node, IfNode):
                if self.evaluate(node.condition, scope):
                    return self.evaluate(node.then_block, scope)
                elif node.else_block:
                    return self.evaluate(node.else_block, scope)
                return None      
            if isinstance(node, BlockNode):
                result = None
                local_runtime_scope = memory.SymbolTable(parent=scope)
                for stmt in node.statements:
                    result = self.evaluate(stmt, local_runtime_scope)
                return result
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
                        # 取出當前參數值
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
                        i += 2 # 跳過 % 和佔位符
                    else:
                        result += fmt[i]
                        i += 1
                        
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
                    # 強制補上結尾符 \0[cite: 17]
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
                for_runtime_scope = memory.SymbolTable(parent=scope)
                
                # 2. 執行初始化 (關鍵：傳入 for_runtime_scope)
                # 如果 node.init 是 int i = 0，i 就會被定義在 for_runtime_scope 裡
                if node.init:
                    self.evaluate(node.init, for_runtime_scope)
                
                last_result = None
                while True:
                    # 3. 檢查條件 (也必須在 for_runtime_scope 裡找 i)
                    if node.condition:
                        condition_val = self.evaluate(node.condition, for_runtime_scope)
                        if not condition_val:
                            break
                    
                    # 4. 執行主體
                    # 注意：如果 body 是 BlockNode ({...})，它會建立自己的子作用域，
                    # 其 parent 會指向我們這裡的 for_runtime_scope，所以能找到 i。
                    last_result = self.evaluate(node.body, for_runtime_scope)
                    
                    # 5. 更新表達式 (i = i + 1)
                    if node.update:
                        self.evaluate(node.update, for_runtime_scope)
                        
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
                if node.op == 'MOD': return left_val - (int(left_val / right_val) * right_val)
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