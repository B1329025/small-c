from lexar import token_map, preprocess
from parser import Parser
from evaluator import Evaluator
import memory

def start_repl():
    global_scope = memory.SymbolTable(parent=None)
    engine = Evaluator()
    print("--- 迷你編譯器互動環境 (輸入 'exit' 退出) ---")
    
    buffer = "" # 用來存放未完成的程式碼
    brace_level = 0 # 追蹤大括號層級

    while True:
        try:
            prompt = ">> " if brace_level == 0 else "... "
            line = input(prompt)
            
            if line.lower() in ('exit', 'quit'):
                break
            
            buffer += line + "\n"
            
            # 計算目前大括號的開閉狀態
            brace_level += line.count('{')
            brace_level -= line.count('}')

            # 只有當所有大括號都閉合了，才開始解析與執行
            if brace_level == 0 and buffer.strip():
                tokens = token_map(preprocess(buffer))
                parser = Parser(tokens)
                parser.current_scope = global_scope
                parser.set_evaluator(engine)

                while parser.pos < len(tokens):
                    node = parser.parse_statement()
                    if node:
                        engine.evaluate(node, global_scope)
                
                buffer = "" # 執行完畢，清空緩衝區
                print() # 確保輸出美觀

        except Exception as e:
            print(f"錯誤：{e}")
            buffer = "" # 發生錯誤時清空緩衝區，避免死鎖
            brace_level = 0

if __name__ == "__main__":
    start_repl()
