import re
from typing import NamedTuple
from nodes import*
from memory import*

class Token(NamedTuple):
    type: str
    value: any
    line: int

class Lexer:
    macros = {}
    def __init__(self, code):
        # 這裡呼叫你原本的處理邏輯
        self.tokens = self.token_map(self.preprocess(code))
        self.tokens.append(Token('EOF', None, -1)) # 加入結束標記

    def __iter__(self):
        return iter(self.tokens)
    def preprocess(self,code):
        lines = code.split('\n')
        new_lines = []
        for line in lines:
            if line.strip().startswith('#define'):
                # 拆解 #define MAX 100
                parts = line.split(maxsplit=2)  
                if len(parts) == 3:
                    _, name, value = parts
                    self.macros[name] = value
                new_lines.append("") #加入空行保持行數一致，然後跳過這回合
                continue
            
            # 進行替換：將程式碼中的 MAX 換成 100
            processed_line = line
            for name, value in self.macros.items():
                # 使用正則替換，確保不會誤換到 ID 的一部分（例如 MAX_VAL 不應被換掉）
                processed_line = re.sub(r'\b' + name + r'\b', value, processed_line)
            new_lines.append(processed_line)
        
        return '\n'.join(new_lines)

    def token_map(self,code):
        token_type=[
            #長度>1
            ('COMMENT', r'/\*[\s\S]*?\*/|//.*'),
            ('STRING', r'"(?:\\.|[^"])*"'),
            ('CHAR', r"'(?:\\.|[^'])'"),
            ('NEWLINE', r'\n'),
            ('SKIP', r'[ \t\r]+'),

            ('PA', r'\+='),
            ('MA' , r'-='),
            ('TA' , r'\*='),
            ('DA' , r'/='),
            ('MOD_A' , r'%='),
            ('LE' , r'<='),
            ('GE' , r'>='),
            ('ls' , r'<<'),
            ('rs' , r'>>'),
            ('E' , r'=='),
            ('NE' , r'!='),
            ('LOGICAL_AND' , r'&&'),
            ('LOGICAL_OR' , r'\|\|'),

            ('NOT', r'!'),
            ('BIT_AND' , r'&'),
            ('OR' , r'\|'),
            ('XOR', r'\^'),
            ('BIT_NOT', r'~'),
            ('TO_IF' , r'\?'),
            ('TO_ELSE', r':'),
            ('COMMA' , r','),
            
            ('LPAREN' , r'\('),
            ('RPAREN' , r'\)'),
            ('LBRACKET' , r'\['),
            ('RBRACKET' , r'\]'),
            ('LBRACES' , r'{'),
            ('RBRACES' , r'}'),

            ('L' , r'<'),
            ('G' , r'>'),
            ('assign', r'='),
            ('PLUS', r'\+'),  # " + "   前面多一個\是為了不讓compiler 誤以為 他要匹配一次或多次，像'\d+'一樣  
            ('MINUS', r'-'),
            ('TIMES', r'\*'),
            ('DIVIDE',  r'/'),
            ('MOD' ,r'%'),

            ('END' , r';'),
            ('ID' ,  r'[a-zA-Z_]\w*'), 
            ('NUMBER', r'0[xX][0-9a-fA-F]+|[1-9]\d*|0'),  #[1-9]\d*|0' -> 確保數字不是0開頭，但0也能被讀取
            ('MISMATCH', r'.'),
        ]
        KEYWORDS = {'if', 'else', 'while', 'for', 'int', 'char', 'void', 'return', 'break', 'continue','printf','do'}
        master_regex = '|'.join(f'(?P<{name}>{reg})' for name, reg in token_type);

        tokens = []
        line_num = 1
        for mo in re.finditer(master_regex, code):
            kind = mo.lastgroup      # 拿到標籤名，例如 'PLUS'
            value = mo.group()       # 拿到內容，例如 '+'
        
            if kind == 'NEWLINE':
                line_num += 1
                continue
            elif kind == 'SKIP' or kind == 'COMMENT':
                # 處理區塊註解可能包含的換行
                if kind == 'COMMENT' and '/*' in value:
                    line_num += value.count('\n')
                continue
            elif kind == 'MISMATCH':
                raise RuntimeError(f'{value!r} 意外出現在第 {line_num} 行')
            elif kind == 'ID' and value in KEYWORDS:
                kind = value.upper()      
            elif kind == 'NUMBER':
                # 如果是 0x 開頭，用 16 進位轉，否則用 10 進位
                if value.lower().startswith('0x'):
                    value = int(value, 16)
                else:
                    value = int(value)
            # 存入列表
            tokens.append(Token(kind, value, line_num))
        
        return tokens
    


