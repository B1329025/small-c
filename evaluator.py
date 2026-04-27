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
                return memory.storage[info['address']]
            if isinstance(node ,AssignNode):
                val = self.evaluate(node.expression_node, scope)
                info = scope.lookup(node.var_name)
                info['initialized'] = True
                address = info['address']
                memory.storage[address] = val
                return val
            if isinstance(node ,UnaryOpNode):
                if node.op =='DEREF':
                    address = self.evaluate(node.operand, scope)
                    return memory.storage[address]
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
                return memory.storage[base_addr + index]
            if isinstance(node,ArrayAssignNode):
                info = scope.lookup(node.name)
                address = info['address']
                size = info['size']
                index=self.evaluate(node.index_node, scope)
                if index<0 or index>=size:
                    raise RuntimeError(f"索引越界！陣列 {node.name} 長度為 {size}，但存取了索引 {index}")
                val=self.evaluate(node.value_node, scope)
                memory.storage[address + index]=val
                return val
            if isinstance(node,DerefAssignNode):
                target_address = self.evaluate(node.target_node, scope)
                value = self.evaluate(node.value_node, scope)
                if target_address < 0 or target_address >= len(memory.storage):
                    raise RuntimeError(f"區段錯誤 (Segmentation fault): 位址 {target_address}")
                memory.storage[target_address] = value
                return value
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