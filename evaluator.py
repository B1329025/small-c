from nodes import *
from builtin import Builtins
import memory
class BreakException(Exception): pass
class ContinueException(Exception): pass
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value # 攜帶要回傳的值
class Evaluator:
    
    def __init__(self):
        self.functions = {}
        self.global_scope = memory.SymbolTable(parent=None)
        self.builtins = Builtins()
        self.trace_enabled = False
        self.current_scope = self.global_scope
    def reset_state(self):
        self.functions = {}
        self.global_scope = memory.SymbolTable(parent=None)
        memory.reset_memory()
    def execute_top_level(self, nodes):
        result = None
        for node in nodes:
            if isinstance(node, (FunctionDeclarationNode, VarDeclarationNode, ArrayDeclarationNode)):
                self.register_global(node) # 註冊全域宣告
            else:
                # 直接執行陳述句 (如 printf)
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
    def visit_FunctionCallNode(self, node, scope):
        # 1. 取得參數值 (計算每一個 arg 表達式)
        arg_values = [self.evaluate(arg, scope) for arg in node.args]

        # 2. 檢查是否為內建函式 (優先權最高)
        if node.name in self.builtins.mapping:
            # 呼叫 builtin.py 裡的方法
            return self.builtins.mapping[node.name](arg_values)

        # 3. 檢查是否為使用者定義的函式 (如 main, swap 等)
        if node.name in self.functions:
            func_node = self.functions[node.name]
            # 這裡要處理自定義函式的 Scope 跳轉與參數綁定
            return self.execute_user_function(func_node, arg_values)

        raise NameError(f"Runtime Error: Undefined function '{node.name}'")
    def visit_StringNode(self, node):
        # 1. 計算需要分配的空間：字串長度 + 1 (結尾符 \0)
        content = node.value
        size = len(content) + 1
        
        # 2. 呼叫現有的記憶體分配方法 (假設你的 memory 有 allocate_memory)
        addr = memory.allocate_memory(size)
        
        # 3. 將字串內容逐一寫入模擬記憶體
        for i, char in enumerate(content):
            memory.write(addr + i, ord(char))
            
        # 4. 寫入 C 字串的結尾符 \0
        memory.write(addr + len(content), 0)
        
        return addr
    def execute_statement(self, node):
        if self.trace_enabled:
            print(f"[Line {node.lineno}] {node.source_code}")
    def execute_user_function(self, func_node, arg_values):
        # 建立函式獨立的作用域
        func_scope = memory.SymbolTable(parent=self.global_scope)
        
        # 這裡需要實作參數綁定 (假設你的 Parser 有解析參數名稱)
        # 暫時先執行主體
        try:
            return self.evaluate(func_node.body, func_scope)
        except ReturnException as e:
            return e.value # 捕捉 return 訊號並回傳數值        

    def evaluate(self,node,scope):
            if node is None:  
                return None
            if isinstance(node, BreakNode):
                raise BreakException()
            if isinstance(node, ContinueNode):
                raise ContinueException()
            if isinstance(node, ReturnNode):
                val = self.evaluate(node.value_node, scope) if node.value_node else 0
                raise ReturnException(val)
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
                result = None
                while self.evaluate(node.condition, scope):
                    try:
                        result = self.evaluate(node.then_block, scope)
                    except BreakException:
                        break # 中斷 Python 的 while 迴圈
                    except ContinueException:
                        continue # 跳過本次循環，進入下一次 condition 判斷
                return result  
            if isinstance(node, ForNode):
                result = None
                # 1. 執行初始化
                self.evaluate(node.init, scope)
                # 2. 進入迴圈
                while self.evaluate(node.condition, scope):
                    try:
                        result = self.evaluate(node.body, scope)
                    except BreakException:
                        break
                    except ContinueException:
                        pass # 跳到更新步驟
                    
                    # 3. 執行更新表達式 (i = i + 1)
                    self.evaluate(node.update, scope)
                return result
            if isinstance(node, FunctionCallNode):
                return self.visit_FunctionCallNode(node, scope)
            if isinstance(node, StringNode):
                return self.visit_StringNode(node)
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
                return self.builtins.printf(node.format_string, arg_values)
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