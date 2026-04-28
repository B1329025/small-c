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
                val = self.evaluate(node.expression_node, scope)
                info = scope.lookup(node.var_name)
                if info is None:
                    raise NameError(f"變數 '{node.var_name}' 尚未宣告過！")
                var_type = info.get('type')
                if var_type == 'int':
                    val = int(val)
                elif var_type == 'char':
                        val = int(val) % 256
                info['initialized'] = True
                address = info['address']
                memory.write(info['address'], val)
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
                # 1. 取得數值 (如果是 c，會得到 65)
                val = self.evaluate(node.expression_node, scope)
                if isinstance(node.expression_node, VarNode):
                    info = scope.lookup(node.expression_node.name)
                    var_type = info.get('type')
                    
                    if var_type == 'int':
                        print(val, end='', flush=True) # 印出數字 3
                    else:
                        print(chr(val), end='', flush=True) # 印出字元 'A'
                else:
                    if isinstance(node.expression_node, NumberNode):
                        raise TypeError("printf 預期收到變數或字串，而非直接的整數常數")
                    
                return None
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
