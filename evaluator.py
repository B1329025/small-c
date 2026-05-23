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
        self.call_depth = 0             
        self.current_function_name = '' 
        self.source_lines = []
    def set_trace(self, enabled):
        """開啟或關閉語句追蹤模式"""
        self.trace_enabled = enabled

    def get_global_variables(self):
        """回傳全域變數狀態以供 VARS 指令顯示"""
        # 遍歷全域符號表，並讀取記憶體中的實際數值
        vars_info = {}
        for name, info in self.global_scope.symbols.items():
            # 讀取當前記憶體中的值
            current_val = memory.read(info['address']) if info.get('address') is not None else None
            
            vars_info[name] = {
                'type': info.get('type'),
                'value': current_val,
                'address': info.get('address'),
                'is_array': info.get('type') == 'array',
                'is_pointer': 'ptr' in str(info.get('type'))
            }
        return vars_info

    def get_defined_functions(self):
        """回傳所有定義的函式以供 FUNCS 指令顯示"""
        func_list = []
        seen_functions = set()  # 用於避免 REPL 緩衝區與全域符號表重複計入

        # 1. 加入內建函式
        for name in self.builtins.mapping:
            func_list.append({
                'name': name, 'type': 'int', 'params': [{'type': '...', 'name': '...'}],
                'line_num': 0, 'is_builtin': True
            })
            seen_functions.add(name)

        # 2. 加入使用者定義函式（來源 A：從全域符號表 global_scope 讀取）
        for name, node in self.global_scope.get_all_functions().items():
            if name in seen_functions:
                continue
            
            params = []
            if hasattr(node, 'params'):
                for p in node.params:
                    p_name = p['name'] if isinstance(p, dict) else getattr(p, 'var_name', str(p))
                    params.append({'type': 'int', 'name': p_name})

            func_list.append({
                'name': name,
                'type': 'int', 
                'params': params,
                'line_num': getattr(node, 'lineno', "??"),
                'is_builtin': False
            })
            seen_functions.add(name)

        # 3. 加入使用者定義函式（來源 B：從 REPL 即時模式快取 self.functions 讀取）
        for name, node in self.functions.items():
            if name in seen_functions:
                continue
                
            params = []
            if hasattr(node, 'params'):
                for p in node.params:
                    p_name = p['name'] if isinstance(p, dict) else getattr(p, 'var_name', str(p))
                    params.append({'type': 'int', 'name': p_name})

            func_list.append({
                'name': name,
                'type': 'int', 
                'params': params,
                'line_num': getattr(node, 'lineno', "??"),
                'is_builtin': False
            })
            seen_functions.add(name)

        return func_list
    def reset_state(self):
        self.global_scope = memory.SymbolTable(parent=None)
        memory.reset_memory()
    def execute_top_level(self, nodes):
        # 1. 第一階段：註冊所有的全域宣告 (變數、陣列、函式)
        for node in nodes:
            if isinstance(node, (FunctionDeclarationNode, VarDeclarationNode, ArrayDeclarationNode)):
                self.register_global(node)
        for node in nodes:
            if not isinstance(node, (FunctionDeclarationNode, VarDeclarationNode, ArrayDeclarationNode)):
                self.evaluate(node, self.global_scope)
        # 2. 第二階段：如果存在 main 函式，則執行它
        main_node = self.global_scope.lookup_function('main')
        if main_node:
            main_scope = memory.SymbolTable(parent=self.global_scope)
            try:
                self.current_function_name = 'main'
                self.call_depth = 0
                return self.evaluate(main_node.body, main_scope)
            except ReturnException as e:
                return e.value
        return None
    

    def register_global(self, node):
        if isinstance(node, FunctionDeclarationNode):
            self.global_scope.define_function(node.name, node)
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
        main_node = self.global_scope.lookup_function('main')   
        if not main_node:
            raise RuntimeError("錯誤：未定義 main() 函式")
        main_scope = memory.SymbolTable(parent=self.global_scope)
        return self.evaluate(main_node.body, main_scope)
    def calculate_compound(self, current_val, rhs_val, op):
        # 確保初始值為 0 而非 None
        c_val = current_val if current_val is not None else 0
        r_val = rhs_val if rhs_val is not None else 0
        
        if op == 'PA':      return c_val + r_val
        if op == 'TA':      return c_val * r_val
        if op == 'MA':      return c_val - r_val
        if op == 'DA':
            if r_val == 0: raise ZeroDivisionError("分母不可是零")
            return int(c_val / r_val)
        if op == 'MOD_A':   
            if r_val == 0: raise ZeroDivisionError("分母不可是零")
            return c_val % r_val
        raise RuntimeError(f"未知的指定運算子: {op}")
    def visit_FunctionCallNode(self, node, scope):
        if node.name == "sizeof_int":
            if len(node.args) != 0:
                raise RuntimeError(f"錯誤：{node.name}() 不需要也不允許輸入任何參數")
            # 既然沒有參數，直接呼叫內建函式（空載），不傳入任何 argument 列表
            return self.builtins.mapping[node.name]()
                
        if node.name == 'sizeof_char':
            if len(node.args) != 0:
                raise RuntimeError(f"錯誤：{node.name}() 不需要也不允許輸入任何參數")
            # 既然沒有參數，直接呼叫內建函式（空載），不傳入任何 argument 列表
            return self.builtins.mapping[node.name]()
        # 1. 取得參數值 (計算每一個 arg 表達式)
        arg_values = [self.evaluate(arg, scope) for arg in node.args]

        # 2. 檢查是否為內建函式 (優先權最高)
        if node.name in self.builtins.mapping:
            # 呼叫 builtin.py 裡的方法
            return self.builtins.mapping[node.name](arg_values)

        # 3. 檢查是否為使用者定義的函式 (如 main, swap 等)
        func_node = scope.lookup_function(node.name)
        if func_node is None:
            # 這裡要處理自定義函式的 Scope 跳轉與參數綁定
            func_node = self.functions.get(node.name)
        if func_node:
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
    def is_pointer(self, node, scope):
        # 情況 1: 直接是變數節點，檢查其符號表中的型別
        if isinstance(node, VarNode):
            info = scope.lookup(node.name)
            return info and (info.get('type') == 'array' or "ptr" in str(info.get('type')))
        
        # 情況 2: 取位址運算 (&a)
        if isinstance(node, UnaryOpNode) and node.op == 'ADDRESS_OF':
            return True
        
        # 情況 3: 巢狀運算 (p + 1) 本身產生的結果也是指標
        if isinstance(node, BinOpNode) and node.op in ('PLUS', 'MINUS'):
            return self.is_pointer(node.left, scope) or self.is_pointer(node.right, scope)
            
        return False
    def execute_statement(self, node):
        if self.trace_enabled:
            print(f"[Line {node.lineno}] {node.source_code}")
    def execute_user_function(self, func_node, arg_values):
        # 建立函式的獨立作用域 (parent 設為 global_scope 符合 C 規範)
        func_scope = memory.SymbolTable(parent=self.global_scope)
        
        for i, param_data in enumerate(func_node.params):
            val = arg_values[i]  # 這裡可能是數值 (int) 或位址 (指向陣列)
            
            # 取得參數名稱與型別
            if isinstance(param_data, dict):
                p_name = param_data['name']
                p_type = f"{param_data['type']}_ptr" if param_data.get('is_ptr') else param_data['type']
            else:
                p_name = getattr(param_data, 'var_name', str(param_data))
                p_type = getattr(param_data, 'var_type', 'int')

            # --- 關鍵修正：為參數分配真實記憶體位址 ---
            # 即使是參數，它在 stack 上也應該有自己的位置
            addr = memory.allocate_memory(1) 
            memory.write(addr, val)  # 將傳入的「值」或「陣列首位址」存入該位置
            
            func_scope.define(p_name, {
                'address': addr,     # 現在 address 不再是 None 了
                'type': p_type, 
                'size': 1,
                'is_param': True,    
                'initialized': True 
            })
        old_func = getattr(self, 'current_function_name', '')
        self.current_function_name = func_node.name
        self.call_depth += 1
        try:
            return self.evaluate(func_node.body, func_scope)
        except ReturnException as e:
            return e.value
        finally:
            self.call_depth -= 1
            self.current_function_name = old_func
    def evaluate(self,node,scope):
            if node is None:  
                return None
            if self.trace_enabled and hasattr(node, 'lineno') and node.lineno:
                # 1. 忽略不需要印出的區塊與函式宣告節點
                if not isinstance(node, (BlockNode, FunctionDeclarationNode, ArrayDeclarationNode)):
                    # 2. 依右圖特例：在非 main 函式中，未初始化的變數宣告（如 int temp;）不印出
                    if isinstance(node, VarDeclarationNode) and not node.init_node and getattr(self, 'current_function_name', '') != 'main':
                        pass
                    else:
                        line_idx = node.lineno - 1
                        if hasattr(self, 'source_lines') and 0 <= line_idx < len(self.source_lines):
                            line_code = self.source_lines[line_idx].strip()
                            indent = "   " * getattr(self, 'call_depth', 0)  # 每層呼叫多 3 個空格
                            print(f"{indent}[line {node.lineno}] {line_code}")
            if isinstance(node, VarDeclarationNode):
                addr = memory.allocate_memory(1)
                # 計算初始值，若無則預設為 0
                val = self.evaluate(node.init_node, scope) if node.init_node else 0
                memory.write(addr, val)
                scope.define(node.var_name, {
                    'address': addr, 'type': node.var_type, 'size': 1, 'initialized': True 
                })
                return val  # 修正：必須回傳 val 而非 None
            # 在 evaluator_19.py 的 evaluate 方法內
            if isinstance(node, FunctionDeclarationNode):
                # 將函式節點儲存到 evaluator 的 functions 字典中，以函式名稱作為 Key
                scope.define_function(node.name, node)
                self.functions[node.name] = node
                # 宣告函式不需要回傳任何執行結果，直接回傳 None
                return None
            if isinstance(node, ArrayDeclarationNode):
                # 1. 計算陣列大小（執行 size_node 得到數值）
                size = self.evaluate(node.size_node, scope)
                
                # 2. 在模擬記憶體中分配連續空間
                addr = memory.allocate_memory(size)
                
                # 3. 將陣列資訊定義在當前作用域 (scope)
                scope.define(node.var_name, {
                    'type': 'array', 
                    'address': addr, 
                    'size': size, 
                    'initialized': False
                })
                
                # 4. 如果有初始值（例如字串賦值），則進行處理
                if node.init_node:
                    init_val = self.evaluate(node.init_node, scope)
                    # 這裡可以實作陣列初始化的邏輯
                    
                return addr
            if isinstance(node, BreakNode):
                raise BreakException()
            if isinstance(node, ContinueNode):
                raise ContinueException()
            if isinstance(node, ReturnNode):
                val = self.evaluate(node.value_node, scope) if node.value_node else 0
                raise ReturnException(val)
            if isinstance(node ,NumberNode):
                return node.value
            # 在 evaluate 方法內的 if isinstance(node, VarNode): 區塊中
            if isinstance(node, VarNode):
                info = scope.lookup(node.name)
                if not info: raise NameError(f"未定義: {node.name}")
                
                # 情況 A：非參數的陣列宣告 (例如 main 裡的 int data[8])
                # 這類變數的 address 直接就是資料起始點
                if info.get('type') == 'array' and not info.get('is_param'): 
                    return info['address']
                
                # 情況 B：一般變數 或 參數（指標）
                # 因為 execute_user_function 已分配空間，這裡一律從記憶體讀取內容
                val = memory.read(info['address'])
                return val if val is not None else 0
            if isinstance(node, AssignNode):
                target_addr = None
                
                if isinstance(node.left, ArrayAccessNode):
                    # 修正處：必須與 ArrayAccessNode 的讀取邏輯一致
                    info = scope.lookup(node.left.name)
                    if not info: raise NameError(f"未定義陣列: {node.left.name}")
                    
                    # 取得基底位址：若是參數或指標，要從記憶體讀出其指向的位址
                    if info.get('is_param') or "ptr" in str(info.get('type')):
                        base_addr = memory.read(info['address'])
                    else:
                        base_addr = info['address']
                        
                    idx = self.evaluate(node.left.index_node, scope)
                    target_addr = base_addr + (int(idx) if idx is not None else 0)
                    
                elif isinstance(node.left, VarNode):
                    info = scope.lookup(node.left.name)
                    if not info: raise NameError(f"未定義變數 {node.left.name}")
                    target_addr = info['address']
                elif isinstance(node.left, UnaryOpNode) and node.left.op == 'DEREF':
                    # 處理 *p = 10
                    target_addr = self.evaluate(node.left.operand, scope)

                # 計算右值並寫回[cite: 31]
                rhs_val = self.evaluate(node.right, scope)
                rhs_val = int(rhs_val) if rhs_val is not None else 0
                
                # 處理 +=, -= 等複合運算
                if node.op != 'assign':
                    cur = memory.read(target_addr)
                    rhs_val = self.calculate_compound(cur or 0, rhs_val, node.op)
                
                memory.write(target_addr, int(rhs_val))
                return rhs_val
            if isinstance(node ,UnaryOpNode):
                if node.op == 'DEREF':
                    target = self.evaluate(node.operand, scope)
                    return memory.read(target)
                if node.op == 'ADDRESS_OF':
                    if isinstance(node.operand, VarNode):
                        return scope.lookup(node.operand.name)['address']
                    if isinstance(node.operand, ArrayAccessNode):
                        # 這裡的邏輯要參考你 ArrayAccessNode 的讀取邏輯
                        info = scope.lookup(node.operand.name)
                        if info.get('is_param') or "ptr" in str(info.get('type')):
                            base_addr = memory.read(info['address'])
                        else:
                            base_addr = info['address']
                        index = self.evaluate(node.operand.index_node, scope)
                        return base_addr + (int(index) if index is not None else 0)
                if node.op =='NEGATIVE':
                    val =self.evaluate(node.operand,scope)
                    return -val
                if node.op =='BIT_NOT':
                    val =self.evaluate(node.operand,scope)
                    return ~val
                if node.op =='NOT':
                    val =self.evaluate(node.operand,scope)
                    return 1 if val==0 else 0
                if node.op in ('PRE_INC', 'PRE_DEC'):
                    # 1. 找出運算目標的記憶體實體位址 (支援變數、陣列元素、指標解引用)
                    target_addr = None
                    
                    if isinstance(node.operand, VarNode):
                        info = scope.lookup(node.operand.name)
                        if not info: raise NameError(f"未定義變數: {node.operand.name}")
                        target_addr = info['address']
                        
                    elif isinstance(node.operand, ArrayAccessNode):
                        info = scope.lookup(node.operand.name)
                        if not info: raise NameError(f"未定義陣列: {node.operand.name}")
                        if info.get('is_param') or "ptr" in str(info.get('type')):
                            base_addr = memory.read(info['address'])
                        else:
                            base_addr = info['address']
                        idx = self.evaluate(node.operand.index_node, scope)
                        target_addr = base_addr + (int(idx) if idx is not None else 0)
                        
                    elif isinstance(node.operand, UnaryOpNode) and node.operand.op == 'DEREF':
                        target_addr = self.evaluate(node.operand.operand, scope)
                    else:
                        raise RuntimeError("錯誤：遞增/遞減運算子必須用於左值 (L-value)")

                    # 2. 讀出舊值，並根據 op 計算出新值
                    current_val = memory.read(target_addr)
                    current_val = current_val if current_val is not None else 0
                    
                    new_val = current_val + 1 if node.op == 'PRE_INC' else current_val - 1
                    
                    # 3. 寫回記憶體，並回傳新值 (符合前綴遞增減特性)
                    memory.write(target_addr, int(new_val))
                    return new_val
            if isinstance(node, IfNode):
                if self.evaluate(node.condition, scope):
                    return self.evaluate(node.then_block, scope)
                elif node.else_block:
                    return self.evaluate(node.else_block, scope)
                return None      
            if isinstance(node, BlockNode):
                res = 0
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
            if isinstance(node, DoWhileNode):
                result = None
                while True:
                    try:
                        result = self.evaluate(node.body, scope)
                    except BreakException: break
                    except ContinueException: pass 
                    
                    if not self.evaluate(node.condition, scope):
                        break
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
            if isinstance(node, ArrayAccessNode):
                 # 直接查找符號表取得位址資訊
                info = scope.lookup(node.name)
                if not info: raise NameError(f"未定義陣列: {node.name}")
                
                if info.get('is_param') or "ptr" in str(info.get('type')):
                    # 參數型陣列：內容存的是指向別處的位址[cite: 31]
                    base_addr = memory.read(info['address'])
                else:
                    # 一般宣告陣列：address 就是首位址[cite: 32]
                    base_addr = info['address']
                    
                index = self.evaluate(node.index_node, scope)
                index = int(index) if index is not None else 0
                
                val = memory.read(base_addr + index)
                return val if val is not None else 0
            
            if isinstance(node, PrintNode):
                # 1. 先計算所有參數的值
                arg_values = [self.evaluate(arg, scope) for arg in node.args]
                return self.builtins.printf(node.format_string, arg_values)
            if isinstance(node, BinOpNode):
                # --- 1. 處理具有短路特性的邏輯運算 (必須先做，不能先 evaluate 右邊) ---
                if node.op == 'LOGICAL_AND':
                    left_val = self.evaluate(node.left, scope)
                    left_val = left_val if left_val is not None else 0
                    if left_val == 0: return 0
                    right_val = self.evaluate(node.right, scope)
                    right_val = right_val if right_val is not None else 0
                    return 1 if right_val != 0 else 0

                if node.op == 'LOGICAL_OR':
                    left_val = self.evaluate(node.left, scope)
                    left_val = left_val if left_val is not None else 0
                    if left_val != 0: return 1
                    right_val = self.evaluate(node.right, scope)
                    right_val = right_val if right_val is not None else 0
                    return 1 if right_val != 0 else 0

                # --- 2. 一般運算：計算數值並強制修正 NoneType ---
                # 注意：這裡只呼叫一次 evaluate，避免副作用
                left_raw = self.evaluate(node.left, scope)
                right_raw = self.evaluate(node.right, scope)
                
                left_val = int(left_raw) if left_raw is not None else 0
                right_val = int(right_raw) if right_raw is not None else 0

                # --- 3. 執行具體運算 (含指標邏輯) ---
                if node.op == 'PLUS': 
                    # 這裡是為了支援指標運算：address + offset
                    return left_val + right_val
                
                if node.op == 'MINUS':
                    # 這裡是為了支援指標相減或 address - offset
                    return left_val - right_val
                    
                if node.op == 'TIMES':  return left_val * right_val
                if node.op == 'DIVIDE':
                    if right_val == 0: raise ZeroDivisionError("除以零錯誤")
                    return int(left_val / right_val)
                if node.op == 'MOD': 
                    if right_val == 0: raise ZeroDivisionError("除以零錯誤")
                    return left_val % right_val
                
                # 位元運算
                if node.op == 'BIT_AND': return left_val & right_val
                if node.op == 'OR':      return left_val | right_val
                if node.op == 'XOR':     return left_val ^ right_val
                if node.op == 'ls':      return left_val << right_val
                if node.op == 'rs':      return left_val >> right_val
                
                # 比較運算：現在 left_val 與 right_val 確保都是 int
                if node.op == 'E':  return 1 if left_val == right_val else 0
                if node.op == 'NE': return 1 if left_val != right_val else 0
                if node.op == 'L':  return 1 if left_val < right_val else 0
                if node.op == 'G':  return 1 if left_val > right_val else 0
                if node.op == 'LE': return 1 if left_val <= right_val else 0
                if node.op == 'GE': return 1 if left_val >= right_val else 0         
            raise RuntimeError(f"未知的節點類型：{type(node)}")