

class Token:
    def __init__(self, kind, value, line):
        self.type = kind
        self.value = value
        self.line = line

    def __repr__(self):
        return f'Token({self.type}, {repr(self.value)}, line={self.line})'
class NumberNode:
    def __init__(self, value): self.value = value

class BinOpNode:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class VarNode:
    def __init__(self, name): self.name = name
class AssignNode:
    def __init__(self, var_name, expression_node):
        self.var_name = var_name
        self.expression_node = expression_node
class UnaryOpNode:
    def __init__(self, op, operand):
        self.op = op          # 運算子，例如 'DEREF' 或 'ADDRESS_OF'
        self.operand = operand # 作用對象
class IfNode:
    def __init__(self ,condition,then_block,else_block):
        self.condition= condition
        self.then_block=then_block
        self.else_block=else_block
class BlockNode:
    def __init__(self, statements):
        self.statements = statements
class WhileNode:
    def __init__(self,condition,then_block):
        self.condition =condition
        self.then_block=then_block
class ArrayAccessNode:
    def __init__(self, name, index_node):
        self.name = name
        self.index_node = index_node
class ArrayAssignNode:
    def __init__(self, name, index_node,value_node):
        self.name = name
        self.index_node = index_node
        self.value_node=value_node
class DerefAssignNode:
    def __init__(self,target_node,value_node):
        self.target_node=target_node
        self.value_node=value_node
class PrintNode:
    def __init__(self, expression_node):
        self.expression_node = expression_node
class StringNode:
    def __init__(self, value):
        self.value = value