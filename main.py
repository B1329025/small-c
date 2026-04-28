from lexar import token_map, preprocess
from parser import Parser
from evaluator import Evaluator
import memory

def start_repl():
    # 初始化全域環境
    global_scope = memory.SymbolTable(parent=None)
    engine = Evaluator()
    
    print("--- 迷你編譯器互動環境 (輸入 'exit' 退出) ---")
    
    while True:
        try:
            # 取得終端機輸入
            code = input(">> ")
            if code.lower() in ('exit', 'quit'):
                break
            if not code.strip():
                continue

            # 處理與執行
            tokens = token_map(preprocess(code))
            parser = Parser(tokens)
            parser.set_evaluator(engine)
            parser.current_scope = global_scope # 保持作用域連續，變數才不會消失

            while parser.pos < len(tokens):
                node = parser.parse_statement()
                if node:
                    engine.evaluate(node, global_scope)
            
            # 這裡不主動印出變數狀態，只執行 node (例如 printf 產生的輸出)
            # 如果 printf 沒換行，我們幫他在輸入下一行前補個換行
            print() 

        except Exception as e:
            print(f"錯誤：{e}")

if __name__ == "__main__":
    start_repl()