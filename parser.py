from nodes import *
import memory
class Parser:
    def set_evaluator(self, evaluator):
        self.evaluator = evaluator
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_scope = memory.SymbolTable(parent=None)
    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def eat(self, token_type):
        #檢查目前的 Token 是否正確，正確就前進一步
        token = self.current_token()
        if token and token.type == token_type:
            self.pos += 1
            return token
        raise SyntaxError(f"語法錯誤：預期 {token_type}，但得到 {token}")
    def parse_statement(self):
        token = self.current_token()
        if not token: return None
        if token.type == 'END':
            self.eat('END')
            return None
        if token.type == 'LBRACES': 
            self.eat('LBRACES')
            statements = []
            new_scope = memory.SymbolTable(parent=self.current_scope)
            previous_scope = self.current_scope
            self.current_scope = new_scope
            while self.current_token() and self.current_token().type != 'RBRACES':
                statements.append(self.parse_statement())
            self.eat('RBRACES')
            block_node = BlockNode(statements)
            block_node.scope = new_scope
            self.current_scope = previous_scope
            return block_node
        if token.type in ('ID', 'TIMES'):
            return self.assign_value()
        if token and token.type =='INT':
            node = self.declare_variable()
            if node: return node # 如果有賦值(回傳了 AssignNode)，回傳它
            return self.parse_statement() # 如果是 int b; (回傳 None)，就遞迴執行下一個語句
        if token and token.type =='IF':
            return self.If()
        if token and token.type =='WHILE':
            return self.WHILE()


    #開始建AST
    def array(self):
        self.eat('LBRACKET')
        num=self.logical_or()
        memory.allocate_memory(num)
        self.eat('RBRACKET')

    def WHILE(self):
        self.eat('WHILE')
        self.eat('LPAREN')
        condition=self.logical_or()
        self.eat('RPAREN')
        then_block=self.parse_statement()
        return WhileNode(condition,then_block)

    def If(self):
        self.eat('IF')
        self.eat('LPAREN')
        condition=self.logical_or()
        self.eat('RPAREN')
        then_block=self.parse_statement()
        else_block=None
        if self.current_token() and self.current_token().type == 'ELSE':
            self.eat('ELSE')
            else_block = self.parse_statement() # 解析 else 語句       
        return IfNode(condition, then_block, else_block)
       
      
    def declare_variable(self):
        self.eat('INT')
        is_pointer=False
        while self.current_token() and self.current_token().type == 'TIMES':
            self.eat('TIMES')
            is_pointer = True
        var_name=self.eat('ID').value    
        
        if self.current_token() and self.current_token().type =='LBRACKET':
            self.eat('LBRACKET')
            size_node=self.logical_or()
            self.eat('RBRACKET')
            self.eat('END')
            size=self.evaluator.evaluate(size_node)
            addr = memory.allocate_memory(size)
            self.current_scope.define(var_name, {
                'address': addr,
                'size': size,
                'type': 'array',
                'initialized': False
            })
            return None
        else:
            addr = memory.allocate_memory(1)
            size = 1
            self.current_scope.define(var_name, {
                'address': addr,
                'size': size,
                'type': 'int_ptr' if is_pointer else 'int',
                'initialized': False
            })
            if self.current_token() and self.current_token().type=='assign':
                self.eat('assign')
                value_node=self.logical_or()
                self.eat('END')
                return  AssignNode(var_name , value_node)
            self.eat('END')
            return None

    def assign_value(self):
        if self.current_token() and self.current_token().type=='TIMES':
            self.eat('TIMES')
            target_node=self.logical_or()
            self.eat('assign')
            value_node=self.logical_or()
            self.eat('END')
            return DerefAssignNode(target_node,value_node)
        var_name=self.eat('ID').value
        info = self.current_scope.lookup(var_name)
        if info is None:
            raise NameError(f"變數 '{var_name}' 尚未宣告過！")
        if self.current_token() and self.current_token().type== 'LBRACKET':
            self.eat('LBRACKET')
            index_node=self.logical_or()
            self.eat('RBRACKET')
            self.eat('assign')
            value_node=self.logical_or()
            self.eat('END')
            return ArrayAssignNode(var_name,index_node,value_node)
        self.eat('assign')
        value_node=self.logical_or()
        self.eat('END')
        return  AssignNode(var_name , value_node)   

    def logical_or(self):
        node=self.logical_and()
        while self.current_token() and self.current_token().type in('LOGICAL_OR'):
            op=self.current_token().type
            self.eat(op)
            right_node=self.logical_and()
            node = BinOpNode(left=node, op=op, right=right_node)
        return node   
    def logical_and(self):
        node=self.comparison()
        while self.current_token() and self.current_token().type in ('LOGICAL_AND'):
            op= self.current_token().type
            self.eat(op)
            right_node=self.comparison()
            node = BinOpNode(left=node, op=op, right=right_node)
        return node
    def comparison(self):
        node=self.expression()
        while self.current_token() and self.current_token().type in('LE' ,'GE','E','NE','G','L'):
            op=self.current_token().type
            self.eat(op)
            right_node=self.expression()
            node = BinOpNode(left=node, op=op, right=right_node)
        return node
    
    def expression(self):
        node=self.term()
        while self.current_token() and self.current_token().type in('PLUS', 'MINUS'):
            op=self.current_token().type
            self.eat(op)
            right_node=self.term()
            node = BinOpNode(left=node, op=op, right=right_node)
        return node       
            
    def term(self):
        node=self.factor()
        while self.current_token() and self.current_token().type in('TIMES' ,'DIVIDE'):
            op=self.current_token().type
            self.eat(op)
            right_node=self.factor()
            node = BinOpNode(left=node, op=op, right=right_node)
        return node
    def factor(self):
        #判斷*和&為pointer  如int *a , *a , &a  因為在factor開始執行時看到*或&就代表他不是乘法或位元AND的用法
        if self.current_token().type == 'TIMES':  
            self.eat('TIMES')
            return UnaryOpNode(op='DEREF', operand=self.factor())       
        if self.current_token().type == 'BIT_AND': 
            self.eat('BIT_AND')
            return UnaryOpNode(op='ADDRESS_OF', operand=self.factor())
        
        if self.current_token().type == 'LPAREN':
            self.eat('LPAREN')
            node=self.logical_or()
            self.eat('RPAREN')
            return node
        elif self.current_token().type =='NUMBER':
            return NumberNode(int(self.eat('NUMBER').value))
        elif self.current_token().type =='ID':
            var_name=self.eat('ID').value
            if self.current_token().type =='LBRACKET':
                self.eat('LBRACKET')
                index_node=self.logical_or()
                self.eat('RBRACKET')
                return ArrayAccessNode(var_name ,index_node)
            return VarNode(var_name)
        raise NameError(f"有問題  當中存在非變數or數字or括號or非關係運算子")
