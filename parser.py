from nodes import *
import memory

def process_string_escapes(s):
    """將字串中字面上的 \\n, \\t, \\0, \\" 等真正轉換為對應的控制字元"""
    result = []
    i = 0
    while i < len(s):
        # 當看到反斜線，且後面還有字元時，進行跳脫處理
        if s[i] == '\\' and i + 1 < len(s):
            ch = s[i+1]
            if ch == 'n':    result.append('\n')   # 換行
            elif ch == 't':  result.append('\t')   # Tab 縮排
            elif ch == '0':  result.append('\0')   # 空字元
            elif ch == '\\': result.append('\\')   # 反斜線本身
            elif ch == '"':  result.append('"')    # 雙引號 (解決 \" 的問題)
            elif ch == "'":  result.append("'")    # 單引號
            else:
                result.append(ch) # 如果是未知的跳脫，就直接保留該字元
            i += 2  # 跳過反斜線與被跳脫的字元
        else:
            result.append(s[i])
            i += 1
    return "".join(result)

class Parser:
    def set_evaluator(self, evaluator):
        self.evaluator = evaluator

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def error_line(self):
        token = self.current_token()

        # EOF
        if token and token.type == 'EOF':
            if self.pos > 0:
                return self.tokens[self.pos - 1].line
            return 1

        # 缺 ; 的情況
        if self.pos > 0:
            prev_line = self.tokens[self.pos - 1].line

            # 若目前 token 已經跳到下一行，
            # 錯誤應該屬於上一行
            if token and token.line > prev_line:
                return prev_line

        return token.line if token else 1
    def parse_program(self):
        nodes = []
        while self.current_token() and self.current_token().type != 'EOF':
            # 支援 INT, CHAR, VOID 作為宣告開頭
            if self.current_token().type in ('INT', 'CHAR', 'VOID'):
                node = self.declare_variable()
                # 如果回傳的是函式宣告，它後面接著的是 {}，不該吃分號
                # 如果是變數或陣列宣告，則必須吃掉結尾的分號
                if not isinstance(node, FunctionDeclarationNode):
                    self.eat('END')
            else:
                node = self.parse_statement() 
            if node:
                nodes.append(node)
        return nodes

    def eat(self, token_type):
        token = self.current_token()

        if token and token.type == token_type:
            self.pos += 1
            return token

        raise SyntaxError(
            f"Line {self.error_line()}: "
            f"語法錯誤：預期 {token_type}，但得到 {token}"
        )

    def parse_statement(self):
        token = self.current_token()
        if not token:
            return None
            
        # ✨ 關鍵修改：記錄此語句開始時的行號
        start_line = token.line 
        
        if token.type == 'END':
            self.eat('END')
            return None

        if token.type in ('INT', 'CHAR','VOID'):
            node = self.declare_variable()
            if not isinstance(node, FunctionDeclarationNode):
                self.eat('END')
            if node: node.lineno = start_line
            return node 
        
        if token.type == 'PRINTF':
            node = self.parse_printf()
            if node: node.lineno = start_line
            return node

        if token.type == 'LBRACES':
            self.eat('LBRACES')
            statements = []
            while self.current_token() and self.current_token().type != 'RBRACES':
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            self.eat('RBRACES')
            block_node = BlockNode(statements)
            block_node.lineno = start_line  # 區塊引導行號
            return block_node

        if token.type in ('ID', 'TIMES','LPAREN','PRE_INC', 'PRE_DEC'):
            node = self.assign_value()
            if self.current_token() and self.current_token().type == 'END':
                self.eat('END')
            if node: node.lineno = start_line
            return node

        if token.type == 'IF':
            node = self.If()
            if node: node.lineno = start_line
            return node

        if token.type == 'WHILE':
            node = self.WHILE()
            if node: node.lineno = start_line
            return node

        if token.type =='FOR':
            node = self.FOR()
            if node: node.lineno = start_line
            return node

        if token.type == 'BREAK':
            node = self.parse_break()
            if node: node.lineno = start_line
            return node
            
        if token.type == 'CONTINUE':
            node = self.parse_continue()
            if node: node.lineno = start_line
            return node
            
        if token.type == 'RETURN':
            node = self.parse_return()
            if node: node.lineno = start_line
            return node
            
        if token.type == 'DO':
            self.eat('DO')
            body = self.parse_statement()
            self.eat('WHILE')
            self.eat('LPAREN')
            cond = self.logical_or()
            self.eat('RPAREN')
            self.eat('END') 
            node = DoWhileNode(body, cond)
            node.lineno = start_line
            return node
            
        line = token.line if token else "Unknown"
        raise SyntaxError(f"Line {line}: 無法解析的語句開頭: {token.type}")

    def parse_block(self):
        start_line = self.current_token().line if self.current_token() else None
        self.eat('LBRACES')
        statements = []
        while self.current_token() and self.current_token().type != 'RBRACES':
            stmt = self.parse_statement()
            if stmt: statements.append(stmt)
        self.eat('RBRACES')
        node = BlockNode(statements)
        node.lineno = start_line
        return node

    def parse_break(self):
        self.eat('BREAK')  # 消耗 'break' Token
        self.eat('END')    # 消耗 ';' Token
        return BreakNode()

    def parse_continue(self):
        self.eat('CONTINUE') # 消耗 'continue' Token
        self.eat('END')      # 消耗 ';' Token
        return ContinueNode()

    def parse_return(self):
        self.eat('RETURN')   # 消耗 'return' Token
        value_node = None
        # 如果後面不是分號，代表有回傳值
        if self.current_token() and self.current_token().type != 'END':
            value_node = self.logical_or() 
        self.eat('END')      # 消耗 ';' Token
        return ReturnNode(value_node)

    def declare_variable(self):
        start_line = self.current_token().line if self.current_token() else None
        token = self.eat(self.current_token().type) # 吃掉 int/char/void
        var_base_type = token.value
        
        # 1. 處理變數名稱前的指標星號
        is_pointer = False
        if self.current_token() and self.current_token().type == 'TIMES':
            self.eat('TIMES')
            is_pointer = True
        
        var_name = self.eat('ID').value
        
        # 2. 判斷是否為函式定義
        if self.current_token() and self.current_token().type == 'LPAREN':
            self.eat('LPAREN')
            params = []
            if self.current_token() and self.current_token().type == 'VOID':
                self.eat('VOID')
                if self.current_token() and self.current_token().type != 'RPAREN':
                    raise SyntaxError(
                        f"Line {self.error_line()}: 語法錯誤：void 參數列表不能再宣告其他參數"
                    )
            elif self.current_token() and self.current_token().type in ('INT', 'CHAR'):
                while True:
                    p_type = self.eat(self.current_token().type).value
                    p_is_ptr = False
                    if self.current_token() and self.current_token().type == 'TIMES':
                        self.eat('TIMES')
                        p_is_ptr = True
                    
                    p_name = self.eat('ID').value
                    params.append({'name': p_name, 'type': p_type, 'is_ptr': p_is_ptr})
                    
                    if self.current_token() and self.current_token().type == 'COMMA':
                        self.eat('COMMA')
                    else:
                        break
            self.eat('RPAREN')
            body = self.parse_statement()
            return FunctionDeclarationNode(var_name, params, body, lineno=start_line)
        
        # 3. 處理一般變數或陣列
        final_type_name = f"{var_base_type}_ptr" if is_pointer else var_base_type
        
        if self.current_token() and self.current_token().type == 'LBRACKET':
            self.eat('LBRACKET')
            size_node = self.logical_or()
            self.eat('RBRACKET')
            init_node = None
            if self.current_token() and self.current_token().type == 'assign':
                self.eat('assign')
                init_node = self.logical_or()
            node = ArrayDeclarationNode(var_base_type, var_name, size_node, init_node)
            node.lineno = start_line  # ✨ 綁定行號
            return node
        else:
            init_node = None
            if self.current_token() and self.current_token().type == 'assign':
                self.eat('assign')
                init_node = self.logical_or()
            node = VarDeclarationNode(final_type_name, var_name, init_node)
            node.lineno = start_line  # ✨ 綁定行號
            return node
        
    def assign_value(self):
        left_node = self.logical_or()
        assign_ops = ['assign', 'PA', 'MA', 'TA', 'DA', 'MOD_A']
        if self.current_token() and self.current_token().type in assign_ops:
            op_token = self.eat(self.current_token().type)
            right_node = self.assign_value()        
            return AssignNode(left_node, op_token.type, right_node)    
        
        return left_node

    def parse_printf(self):
        self.eat('PRINTF')
        self.eat('LPAREN')
        format_token = self.eat('STRING')
        format_str = process_string_escapes(format_token.value[1:-1])
        args = []
        while self.current_token() and self.current_token().type == 'COMMA':
            self.eat('COMMA')
            args.append(self.logical_or())
        self.eat('RPAREN')
        self.eat('END')
        return PrintNode(format_str, args)

    def If(self):
        self.eat('IF')
        self.eat('LPAREN')
        condition = self.logical_or()
        self.eat('RPAREN')
        then_block = self.parse_statement()
        else_block = None
        if self.current_token() and self.current_token().type == 'ELSE':
            self.eat('ELSE')
            else_block = self.parse_statement()
        return IfNode(condition, then_block, else_block)

    def WHILE(self):
        self.eat('WHILE')
        self.eat('LPAREN')
        condition = self.logical_or()
        self.eat('RPAREN')
        then_block = self.parse_statement()
        return WhileNode(condition, then_block)

    def FOR(self):
        self.eat('FOR')
        self.eat('LPAREN')
        if self.current_token().type in ('INT', 'CHAR'):
            init = self.declare_variable() 
        else:
            init = self.assign_value()
        self.eat('END') 
        cond = self.logical_or()
        self.eat('END') 
        upd = self.assign_value()
        self.eat('RPAREN')
        
        body = self.parse_statement()
        return ForNode(init, cond, upd, body)

    def logical_or(self):
        node = self.logical_and()
        while self.current_token() and self.current_token().type == 'LOGICAL_OR':
            op = self.eat(self.current_token().type).type
            right_node = self.logical_and()
            node = BinOpNode(node, op, right_node)
        return node

    def logical_and(self):
        node = self.bit_or()
        while self.current_token() and self.current_token().type == 'LOGICAL_AND':
            op = self.eat(self.current_token().type).type
            right_node = self.bit_or()
            node = BinOpNode(node, op, right_node)
        return node

    def bit_or(self):
        node=self.bit_xor()
        while self.current_token() and self.current_token().type =='OR':
            op=self.eat(self.current_token().type).type
            right_node=self.bit_xor()
            node=BinOpNode(node,op,right_node)
        return node

    def bit_xor(self):
        node=self.bit_and()
        while self.current_token() and self.current_token().type =='XOR':
            op=self.eat(self.current_token().type).type
            right_node=self.bit_and()
            node=BinOpNode(node,op,right_node)
        return node

    def bit_and(self):
        node = self.comparison() 
        while self.current_token() and self.current_token().type == 'BIT_AND':
            op = self.eat(self.current_token().type).type
            right_node = self.comparison()
            node = BinOpNode(node, op, right_node)
        return node

    def comparison(self):
        node = self.shift()
        while self.current_token() and self.current_token().type in ('LE', 'GE', 'E', 'NE', 'G', 'L'):
            op = self.eat(self.current_token().type).type
            right_node = self.shift()
            node = BinOpNode(node, op, right_node)
        return node

    def shift(self):
        node =self.expression()
        while self.current_token() and self.current_token().type in ('ls', 'rs'):
            op = self.eat(self.current_token().type).type
            right_node = self.expression()
            node = BinOpNode(node, op, right_node)
        return node

    def expression(self):
        node = self.term()
        while self.current_token() and self.current_token().type in ('PLUS', 'MINUS'):
            op = self.eat(self.current_token().type).type
            right_node = self.term()
            node = BinOpNode(node, op, right_node)
        return node

    def term(self):
        node = self.factor()
        while self.current_token() and self.current_token().type in ('TIMES', 'DIVIDE','MOD'):
            op = self.eat(self.current_token().type).type
            right_node = self.factor()
            node = BinOpNode(node, op, right_node)
        return node

    def factor(self):
        token = self.current_token()
        if token.type =='NOT':
            self.eat('NOT')
            return UnaryOpNode('NOT',self.factor())
        if token.type =='MINUS':
            self.eat('MINUS')
            return UnaryOpNode('NEGATIVE',self.factor())
        if token.type =='BIT_NOT':
            self.eat('BIT_NOT')
            return UnaryOpNode('BIT_NOT',self.factor())
        if token.type == 'TIMES':
            self.eat('TIMES')
            return UnaryOpNode('DEREF', self.factor())
        if token.type == 'BIT_AND':
            self.eat('BIT_AND')
            return UnaryOpNode('ADDRESS_OF', self.factor()) 
        if token.type == 'PRE_INC':
            self.eat('PRE_INC')
            return UnaryOpNode('PRE_INC', self.factor())
        if token.type == 'PRE_DEC':
            self.eat('PRE_DEC')
            return UnaryOpNode('PRE_DEC', self.factor())
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while self.current_token() and self.current_token().type == 'LBRACKET':
            var_name = node.name if isinstance(node, VarNode) else node.name
            self.eat('LBRACKET')
            index_node = self.logical_or()
            self.eat('RBRACKET')
            node = ArrayAccessNode(var_name, index_node)
        return node

    def primary(self):
        token = self.current_token()  
        
        if token.type == 'NUMBER':
            return NumberNode(int(self.eat('NUMBER').value))           
        
        if token.type == 'STRING':
            raw_str = self.eat('STRING').value[1:-1]
            return StringNode(process_string_escapes(raw_str))
            
        if token.type == 'CHAR':
            token_val = self.eat('CHAR').value
            content = token_val[1:-1]
            
            if content.startswith('\\') and len(content) >= 2:
                escape_char = content[1]
                escape_map = {
                    'n': 10, 't': 9, '0': 0, '\\': 92, "'": 39, '"': 34
                }
                val = escape_map.get(escape_char, ord(escape_char))
            else:
                val = ord(content) if len(content) > 0 else 0
                
            return NumberNode(val)
            
        if token.type == 'ID':
            name = self.eat('ID').value
            if self.current_token() and self.current_token().type == 'LPAREN':
                self.eat('LPAREN')
                args = []
                if self.current_token().type != 'RPAREN':
                    args.append(self.logical_or())
                    while self.current_token().type == 'COMMA':
                        self.eat('COMMA')
                        args.append(self.logical_or())
                self.eat('RPAREN')
                return FunctionCallNode(name, args)
            
            return VarNode(name)          
            
        if token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.logical_or()
            self.eat('RPAREN')
            return node        
            
        raise SyntaxError(f"無法識別的語法單元: {token}")
