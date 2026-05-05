

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
    def __init__(self, left ,op ,right):
        self.left=left
        self.op=op
        self.right=right
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
    def __init__(self, format_string, args):
        self.format_string = format_string  # 例如 "%d %c"
        self.args = args    # 表達式節點列表 [VarNode('a'), VarNode('b')]
class StringNode:
    def __init__(self, value):
        self.value = value
class ArrayDeclarationNode:
    def __init__(self, var_type, var_name, size_node, init_node=None):
        self.var_type = var_type
        self.var_name = var_name
        self.size_node = size_node # 存儲節點而非數值
        self.init_node = init_node

class VarDeclarationNode:
    def __init__(self, var_type, var_name, init_node=None):
        self.var_type = var_type
        self.var_name = var_name
        self.init_node = init_node
class ForNode:
    def __init__(self, init, condition, update, body):
        self.init = init        # 例如: i = 0
        self.condition = condition  # 例如: i < 10
        self.update = update      # 例如: i = i + 1
        self.body = body        # 迴圈主體
class FunctionDeclarationNode:
    def __init__(self, name, params, body): 
        self.name = name
        self.params = params  # 存儲參數名稱清單，例如 ['n']
        self.body = body
class ProgramNode:
    def __init__(self, declarations):
        self.declarations = declarations
class FunctionCallNode:
    def __init__(self, name, args):
        self.name = name  # 函式名稱，例如 "strcmp"
        self.args = args  # 參數列表，裡面會是其他的 Node
class BreakNode:
    pass
class ContinueNode:
    pass
class ReturnNode:
    def __init__(self, value_node=None):
        self.value_node = value_node # 回傳的表達式節點，例如 return a + 5;
class DoWhileNode:
    def __init__(self, body, condition):
        self.body = body
        self.condition = condition