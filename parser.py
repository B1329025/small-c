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
        token = self.current_token()
        if token and token.type == token_type:
            self.pos += 1
            return token
        raise SyntaxError(f"語法錯誤：預期 {token_type}，但得到 {token}")

    def parse_statement(self):
        token = self.current_token()
        if not token:
            return None

        if token.type in ('INT', 'CHAR'):
            return self.declare_variable()
        
        if token.type == 'PRINTF':
            return self.parse_printf()

        if token.type == 'LBRACES':
            self.eat('LBRACES')
            statements = []
            new_scope = memory.SymbolTable(parent=self.current_scope)
            previous_scope = self.current_scope
            self.current_scope = new_scope
            while self.current_token() and self.current_token().type != 'RBRACES':
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            self.eat('RBRACES')
            block_node = BlockNode(statements)
            block_node.scope = new_scope
            self.current_scope = previous_scope
            return block_node

        if token.type in ('ID', 'TIMES'):
            return self.assign_value()

        if token.type == 'IF':
            return self.If()

        if token.type == 'WHILE':
            return self.WHILE()

        if token.type == 'END':
            self.eat('END')
            return None

        raise SyntaxError(f"無法解析的語句開頭: {token.type}")

    def declare_variable(self):
        token = self.eat(self.current_token().type)
        var_base_type = token.value
        
        is_pointer = False
        while self.current_token() and self.current_token().type == 'TIMES':
            self.eat('TIMES')
            is_pointer = True
        
        var_name = self.eat('ID').value
        final_type_name = f"{var_base_type}_ptr" if is_pointer else var_base_type

        if self.current_token() and self.current_token().type == 'LBRACKET':
            self.eat('LBRACKET')
            size_node = self.logical_or()
            self.eat('RBRACKET')
            size = self.evaluator.evaluate(size_node, self.current_scope)
            addr = memory.allocate_memory(size)
            self.current_scope.define(var_name, {
                'address': addr,
                'size': size,
                'type': 'array',
                'element_type': var_base_type,
                'initialized': False
            })
            
            if self.current_token() and self.current_token().type == 'assign':
                self.eat('assign')
                value_node = self.logical_or()
                self.eat('END')
                return AssignNode(var_name, value_node)
            
            self.eat('END')
            return None
        else:
            addr = memory.allocate_memory(1)
            self.current_scope.define(var_name, {
                'address': addr,
                'size': 1,
                'type': final_type_name,
                'initialized': False
            })
            
            if self.current_token() and self.current_token().type == 'assign':
                self.eat('assign')
                value_node = self.logical_or()
                self.eat('END')
                return AssignNode(var_name, value_node)
            
            self.eat('END')
            return None

    def assign_value(self):
        if self.current_token().type == 'TIMES':
            self.eat('TIMES')
            target_node = self.logical_or()
            self.eat('assign')
            value_node = self.logical_or()
            self.eat('END')
            return DerefAssignNode(target_node, value_node)

        var_name = self.eat('ID').value
        if self.current_token() and self.current_token().type == 'LBRACKET':
            self.eat('LBRACKET')
            index_node = self.logical_or()
            self.eat('RBRACKET')
            self.eat('assign')
            value_node = self.logical_or()
            self.eat('END')
            return ArrayAssignNode(var_name, index_node, value_node)
        
        self.eat('assign')
        value_node = self.logical_or()
        self.eat('END')
        return AssignNode(var_name, value_node)

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

    def logical_or(self):
        node = self.logical_and()
        while self.current_token() and self.current_token().type == 'LOGICAL_OR':
            op = self.eat(self.current_token().type).type
            right_node = self.logical_and()
            node = BinOpNode(node, op, right_node)
        return node

    def logical_and(self):
        node = self.comparison()
        while self.current_token() and self.current_token().type == 'LOGICAL_AND':
            op = self.eat(self.current_token().type).type
            right_node = self.comparison()
            node = BinOpNode(node, op, right_node)
        return node

    def comparison(self):
        node = self.expression()
        while self.current_token() and self.current_token().type in ('LE', 'GE', 'E', 'NE', 'G', 'L'):
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
        while self.current_token() and self.current_token().type in ('TIMES', 'DIVIDE'):
            op = self.eat(self.current_token().type).type
            right_node = self.factor()
            node = BinOpNode(node, op, right_node)
        return node

    def factor(self):
        token = self.current_token()
        if token.type == 'TIMES':
            self.eat('TIMES')
            return UnaryOpNode('DEREF', self.factor())
        if token.type == 'BIT_AND':
            self.eat('BIT_AND')
            return UnaryOpNode('ADDRESS_OF', self.factor())
        if token.type == 'STRING':
            return StringNode(self.eat('STRING').value[1:-1])
        if token.type == 'CHAR':
            return NumberNode(ord(self.eat('CHAR').value[1]))
        if token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.logical_or()
            self.eat('RPAREN')
            return node
        if token.type == 'NUMBER':
            return NumberNode(int(self.eat('NUMBER').value))
        if token.type == 'ID':
            var_name = self.eat('ID').value
            if self.current_token() and self.current_token().type == 'LBRACKET':
                self.eat('LBRACKET')
                index_node = self.logical_or()
                self.eat('RBRACKET')
                return ArrayAccessNode(var_name, index_node)
            return VarNode(var_name)
        raise SyntaxError(f"無法識別的因子: {token}")
