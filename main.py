import sys
from lexar import Lexer
from parser import Parser
from evaluator import Evaluator

def run_interactive_interpreter():
    evaluator = Evaluator()
    user_code_buffer = []
    is_append_mode = False

    print("C-Lite Interpreter (Active)")
    
    while True:
        try:
            # --- 1. 自動感應提示符號邏輯 ---
            current_content = "\n".join(user_code_buffer)
            # 計算大括號是否對齊[cite: 25]
            open_braces = current_content.count('{')
            close_braces = current_content.count('}')
            
            if is_append_mode or open_braces > close_braces:
                prompt = "> "
            else:
                prompt = "sc> "

            line = input(prompt)
            clean_line = line.strip()
            cmd = clean_line.upper()

            # --- 2. 系統指令處理 ---
            if cmd == "EXIT":
                sys.exit(0)
            elif cmd == "APPEND":
                is_append_mode = True
                continue
            elif cmd == "RUN":
                if user_code_buffer:
                    execute_ast("\n".join(user_code_buffer), evaluator)
                    user_code_buffer.clear()
                is_append_mode = False
                continue
            elif cmd == "NEW":
                evaluator.reset_state()
                user_code_buffer.clear()
                is_append_mode = False
                print("Environment reset.")
                continue

            # --- 3. 代碼收集與自動執行 ---
            user_code_buffer.append(line)
            
            # 如果不是手動 APPEND 模式，且括號剛好對齊，則嘗試執行
            if not is_append_mode:
                updated_content = "\n".join(user_code_buffer)
                updated_open = updated_content.count('{')
                updated_close = updated_content.count('}')
                
                # 情境 A: 寫完一個完整的區塊 { ... }[cite: 25, 29]
                if updated_open > 0 and updated_open == updated_close:
                    execute_ast(updated_content, evaluator)
                    user_code_buffer.clear()
                # 情境 B: 一般單行語句（且不含未閉合括號）
                elif updated_open == 0 and updated_close == 0:
                    execute_ast(updated_content, evaluator)
                    user_code_buffer.clear()

        except KeyboardInterrupt:
            print("\nUse EXIT to quit.")
            user_code_buffer.clear()
        except Exception as e:
            print(f"Runtime/Syntax Error: {e}")
            user_code_buffer.clear()

def execute_ast(code, evaluator):
    """將代碼交給 Lexer -> Parser -> Evaluator[cite: 28, 29]"""
    if not code.strip(): return
    lexer = Lexer(code)
    parser = Parser(lexer.tokens)
    ast_nodes = parser.parse_program()
    evaluator.execute_top_level(ast_nodes)

if __name__ == "__main__":
    run_interactive_interpreter()