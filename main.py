from lexar import Lexer
from parser import Parser
from evaluator import Evaluator

import sys

user_code_storage = []

def run_interpreter():
    global user_code_storage
    evaluator = Evaluator() 
    
    while True:
        try:
            line = input(">> ")
            cmd = line.strip()
            if cmd == "EXIT":
                print("Goodbye!")
                sys.exit(0) # 正常退出程式
            if cmd == "RUN":
                code = "\n".join(user_code_storage)
                if not code.strip(): continue
                
                try:
                    lexer = Lexer(code)
                    parser = Parser(lexer.tokens)
                    ast = parser.parse_program()
                    # 修改此行：使用新的互動式執行方法[cite: 18, 20]
                    evaluator.execute_top_level(ast)
                    # 執行完後清空暫存，這樣下次輸入就是新的指令[cite: 20]
                    user_code_storage.clear() 
                    print("\nExecution finished.")
                except Exception as e:
                    print(f"Error: {e}")
            elif cmd == "NEW":
                user_code_storage.clear()
                evaluator.reset_state() # 重置包含記憶體在內的狀態[cite: 16]
                print("Environment cleared.")
            else:
                user_code_storage.append(line)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_interpreter()