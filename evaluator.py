from nodes import *
import memory
class Evaluator:
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
            if isinstance(node ,AssignNode):
                # 取得右值。注意：如果是 StringNode，回傳的是記憶體位址（int）
                val = self.evaluate(node.expression_node, scope)
                info = scope.lookup(node.var_name)
                if info is None:
                    raise NameError(f"變數 '{node.var_name}' 尚未宣告過！")
                
                # 判斷是否為陣列字串初始化：檢查節點類型，而非 evaluate 後的結果
                if info.get('type') == 'array' and isinstance(node.expression_node, StringNode):
                    base_addr = info['address']
                    raw_str = node.expression_node.value # 取得原始字串內容
                    for i, char in enumerate(raw_str):
                        if i < info['size']:
                            memory.write(base_addr + i, ord(char))
                    if len(raw_str) < info['size']:
                        memory.write(base_addr + len(raw_str), 0)
                else:
                    # 一般變數或指標賦值，直接寫入記憶體
                    if info.get('type') != 'array':
                        memory.write(info['address'], val)
                
                # 關鍵修正：確保所有賦值都會標記為已初始化
                info['initialized'] = True
                return val
            if isinstance(node ,UnaryOpNode):
                if node.op =='DEREF':
                    address = self.evaluate(node.operand, scope)
                    return memory.read(address)
                elif node.op =='ADDRESS_OF':
                    info =scope.lookup(node.operand.name)
                    return info['address']

            if isinstance(node, IfNode):
                if self.evaluate(node.condition, scope):
                    return self.evaluate(node.then_block, scope)
                elif node.else_block:
                    return self.evaluate(node.else_block, scope)
                return None      
            if isinstance(node, BlockNode):
                result = None
                target_scope = getattr(node, 'scope', scope)
                for stmt in node.statements:
                    result = self.evaluate(stmt, target_scope)
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
            if isinstance(node,ArrayAssignNode):
                info = scope.lookup(node.name)
                address = info['address']
                size = info['size']
                index=self.evaluate(node.index_node, scope)
                if index<0 or index>=size:
                    raise RuntimeError(f"索引越界！陣列 {node.name} 長度為 {size}，但存取了索引 {index}")
                val=self.evaluate(node.value_node, scope)
                memory.write(address + index, val)
                return val
            if isinstance(node,DerefAssignNode):
                target_address = self.evaluate(node.target_node, scope)
                value = self.evaluate(node.value_node, scope)
                if target_address < 0 or target_address >= len(memory.storage):
                    raise RuntimeError(f"區段錯誤 (Segmentation fault): 位址 {target_address}")
                memory.storage[target_address] = value
                return value
            if isinstance(node, PrintNode):
                # 1. 先計算所有參數的值
                arg_values = [self.evaluate(arg, scope) for arg in node.args]
                
                fmt = node.format_string
                result = ""
                arg_idx = 0
                i = 0
                
                while i < len(fmt):
                    if fmt[i] == '%' and i + 1 < len(fmt):
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
                            while True:
                                char_code = memory.read(addr)
                                if char_code == 0: break
                                s_val += chr(char_code)
                                addr += 1
                            result += s_val
                        i += 2 # 跳過 % 和佔位符
                    else:
                        result += fmt[i]
                        i += 1
                        
                print(result, end='', flush=True)
                return None
            if isinstance(node, ArrayDeclarationNode):
                # 1. 向 memory.py 請求分配連續空間
                base_address = memory.allocate_memory(node.size)
                
                # 2. 如果有初始化字串 (hello)
                if node.init_node and isinstance(node.init_node, StringNode):
                    content = node.init_node.value
                    # 逐字寫入 ASCII 碼
                    for i in range(min(len(content), node.size)):
                        memory.write(base_address + i, ord(content[i]))
                    # 補上 C 語言字串結尾符號 \0 (如果還有空間)
                    if len(content) < node.size:
                        memory.write(base_address + len(content), 0)
                        
                # 3. 註冊到符號表
                scope.define(node.var_name, {
                    'type': 'array',
                    'element_type': node.var_type,
                    'address': base_address,
                    'size': node.size,
                    'initialized': True
                })
                return base_address
            if isinstance(node, StringNode):
                # 1. 在記憶體中分配空間 (字串長度 + 1 個 '\0' 結束符)
                base_address = memory.allocate_memory(len(node.value) + 1)
                # 2. 逐一寫入 ASCII 碼
                for i, char in enumerate(node.value):
                    memory.write(base_address + i, ord(char))
                memory.write(base_address + len(node.value), 0) # 寫入結束符 \0
                return base_address # 回傳字串的首位址
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
                if node.op == 'DIVIDE': return left_val // right_val
                if node.op == 'MINUS': return left_val - right_val
                if node.op == 'E': return 1 if left_val == right_val else 0
                if node.op == 'LE': return 1 if left_val <= right_val else 0
                if node.op == 'GE': return 1 if left_val >= right_val else 0
                if node.op == 'L': return 1 if left_val < right_val else 0
                if node.op == 'G': return 1 if left_val > right_val else 0
                if node.op == 'NE': return 1 if left_val != right_val else 0

            raise RuntimeError(f"未知的節點類型：{type(node)}")
