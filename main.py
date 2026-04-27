from lexar import token_map, preprocess
from parser import Parser
from evaluator import Evaluator
import memory

def run_full_test():

    code = """
    int a = 10;
    int b =2;
    if (a > b){
        int a = 30;
    }
    b=1;
    """
    tokens = token_map(preprocess(code))
    parser = Parser(tokens)
    global_scope = memory.SymbolTable(parent=None)
    parser.current_scope = global_scope
    engine = Evaluator()
    parser.set_evaluator(engine)
    
    print("--- 執行測試 ---")
    try:
        
        while parser.pos < len(tokens):
            current = parser.current_token()
            print(f"DEBUG: 正在處理 Token: {current.type} at line {current.line}")
            node = parser.parse_statement()
            if node:
                engine.evaluate(node,parser.current_scope)
        
        print("執行成功！狀態如下：")
        for name, info in global_scope.symbols.items():
            addr = info['address']
            print(f"變數 {name} (位址 {addr}) = {memory.storage[addr]}")
            
    except Exception as e:
        print(f"錯誤：{e}")
        import traceback
        traceback.print_exc()

# 記得把你的 Parser 類別放在這裡面
run_full_test()