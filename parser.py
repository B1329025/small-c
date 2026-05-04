from nodes import *
import memory

class Parser:
    def set_evaluator(self, evaluator):
        self.evaluator = evaluator

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def parse_program(self):
        nodes = []
        while self.current_token() and self.current_token().type != 'EOF':
            # 嘗試解析宣告，若失敗則解析為一般語句[cite: 22]
            if self.current_token().type in ('INT', 'CHAR'):
                node = self.declare_variable()
                self.eat('END')
            else:
                # 這裡讓它可以解析 printf 或運算式[cite: 22]
                node = self.parse_statement() 
            nodes.append(node)
        return nodes

    def eat(self, token_type):
        token = self.current_token()
        if token and token.type == token_type:
            self.pos += 1
            return token
        raise SyntaxError(f"語法錯誤：預期 {token_type}，但得到 {token}")

    def parse_statement(self):
        token = self.current_token()
        if token.type == 'END':
            self.eat('END')
            return None

        if token.type in ('INT', 'CHAR'):
            node =self.declare_variable()
            self.eat('END')
            return node 
        
        if token.type == 'PRINTF':
            return self.parse_printf()

        if token.type == 'LBRACES':
            self.eat('LBRACES')
            statements = []
            while self.current_token() and self.current_token().type != 'RBRACES':
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            self.eat('RBRACES')
            block_node = BlockNode(statements)
            return block_node

        if token.type in ('ID', 'TIMES'):
            node = self.assign_value()
            self.eat('END')
            return node

        if token.type == 'IF':
            return self.If()

        if token.type == 'WHILE':
            return self.WHILE()

        if token.type =='FOR':
            return self.FOR()
        raise SyntaxError(f"無法解析的語句開頭: {token.type}")
    def parse_block(self):
        self.eat('LBRACES')
        statements = []
        while self.current_token() and self.current_token().type != 'RBRACES':
            stmt = self.parse_statement()
            if stmt: statements.append(stmt)
        self.eat('RBRACES')
        return BlockNode(statements)
        

    def declare_variable(self):
        token = self.eat(self.current_token().type)
        var_base_type = token.value
        
        is_pointer = False
        if self.current_token().type == 'TIMES':
            self.eat('TIMES')
            is_pointer = True
        
        var_name = self.eat('ID').value
        if self.current_token().type == 'LPAREN':
            self.eat('LPAREN')
            # 這裡簡化處理，不處理參數，直接到 ')'
            self.eat('RPAREN')
            body = self.parse_statement() # 解析函式主體 {}
            return FunctionDeclarationNode(var_name, body)
        final_type_name = f"{var_base_type}_ptr" if is_pointer else var_base_type
        
        # 處理陣列宣告: char a[7]
        if self.current_token() and self.current_token().type == 'LBRACKET':
            self.eat('LBRACKET')
            size_node = self.logical_or()
            self.eat('RBRACKET')
            
            init_node = None
            if self.current_token() and self.current_token().type == 'assign':
                self.eat('assign')
                init_node = self.logical_or()
            
            # 僅回傳節點，不執行 define。注意：此處 size 傳入 size_node 給 Evaluator 計算
            return ArrayDeclarationNode(var_base_type, var_name, size_node, init_node)
        
        # 處理一般變數宣告: int a = 5
        else:
            init_node = None
            if self.current_token() and self.current_token().type == 'assign':
                self.eat('assign')
                init_node = self.logical_or()
            
            # 建立一個通用的宣告節點 (需在 nodes.py 定義或直接用一個標示位址的節點)
            return VarDeclarationNode(final_type_name, var_name, init_node)
        
    def assign_value(self):
        if self.current_token().type == 'TIMES':
            self.eat('TIMES')
            left_node = UnaryOpNode('DEREF', self.logical_or())
        else:
            var_name = self.eat('ID').value
            if self.current_token() and self.current_token().type == 'LBRACKET':
                self.eat('LBRACKET')
                index_node = self.logical_or()
                self.eat('RBRACKET')
                left_node =ArrayAccessNode(var_name,index_node)
            else:
                left_node =VarNode(var_name)
        assign_ops =['assign','PA','MA','TA','DA','MOD_A']
        if self.current_token() and self.current_token().type in assign_ops:
            op_token =self.eat(self.current_token().type)
            right_node =self.logical_or()        
            return AssignNode(left_node,op_token.type,right_node)    
        return left_node
    def parse_printf(self):
        self.eat('PRINTF')
        self.eat('LPAREN')
        format_token = self.eat('STRING')
        format_str = format_token.value[1:-1]
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
        # 修正：FOR 的 init 可以是宣告或賦值[cite: 17]
        init = self.declare_variable() if self.current_token().type in ('INT', 'CHAR') else self.assign_value()
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
        return self.postfix()
    def postfix(self):
        node = self.primary()
        while self.current_token() and self.current_token().type == 'LBRACKET':
            var_name = node.name if isinstance(node, VarNode) else None
            self.eat('LBRACKET')
            index_node = self.logical_or()
            self.eat('RBRACKET')
            node = ArrayAccessNode(var_name, index_node)
        return node
    def primary(self):
        """最基礎的原子單元"""
        token = self.current_token()  
        if token.type == 'NUMBER':
            return NumberNode(int(self.eat('NUMBER').value))           
        if token.type == 'STRING':
            return StringNode(self.eat('STRING').value[1:-1])
        if token.type == 'CHAR':
            # 將 'A' 轉為 ASCII 碼
            val = ord(self.eat('CHAR').value[1])
            return NumberNode(val)
        if token.type == 'ID':
            return VarNode(self.eat('ID').value)          
        if token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.logical_or()
            self.eat('RPAREN')
            return node        
        raise SyntaxError(f"無法識別的語法單元: {token}")