from lexar import Lexer
from parser import Parser
from evaluator import Evaluator
import memory
import sys

# 修改後的 main_5.py 核心邏輯
def run_interpreter():
    user_code_storage = []
    evaluator = Evaluator()
    is_append_mode = False 

    while True:
        try:
            # 判斷是否在自動續行或手動 APPEND 模式
            # 檢查緩衝區內所有代碼的大括號配對情況
            current_buffer = "\n".join(user_code_storage)
            open_braces = current_buffer.count('{')
            close_braces = current_buffer.count('}')
            
            # 如果左括號比較多，或是處於 APPEND 模式，就使用 "> " 提示
            if is_append_mode or open_braces > close_braces:
                prompt = "> "
            else:
                prompt = "sc> "

            line = input(prompt)
            clean_line = line.strip()
            cmd = clean_line.upper()

            # 指令判斷
            if cmd == "EXIT":
                sys.exit(0)
            elif cmd == "APPEND":
                is_append_mode = True
                continue
            elif cmd == "NEW":
                user_code_storage.clear()
                evaluator.reset_state()
                is_append_mode = False
                continue
            elif cmd == "RUN":
                # 在手動 APPEND 模式下，輸入 RUN 才會執行
                if user_code_storage:
                    execute_code("\n".join(user_code_storage), evaluator)
                    user_code_storage.clear()
                is_append_mode = False
                continue

            # 核心邏輯：存入緩衝區
            user_code_storage.append(line)

            # 如果不是手動 APPEND 模式，且括號剛好成對（且緩衝區不為空），則自動執行
            if not is_append_mode:
                updated_buffer = "\n".join(user_code_storage)
                if updated_buffer.count('{') == updated_buffer.count('}') and updated_buffer.count('{') > 0:
                    execute_code(updated_buffer, evaluator)
                    user_code_storage.clear()
                elif '{' not in updated_buffer:
                    # 如果根本沒有大括號（一般單行指令），輸入完立刻執行
                    execute_code(updated_buffer, evaluator)
                    user_code_storage.clear()

        except Exception as e:
            print(f"Error: {e}")
            user_code_storage.clear() # 發生錯誤時清空緩衝區以免死鎖

def execute_code(code, evaluator):
    """封裝解析與執行的邏輯[cite: 23, 25]"""
    try:
        lexer = Lexer(code)
        parser = Parser(lexer.tokens)
        ast = parser.parse_program()
        evaluator.execute_top_level(ast) # 執行頂層語句並保留變數狀態[cite: 23]
    except Exception as e:
        print(f"Runtime Error: {e}")

if __name__ == "__main__":
    run_interpreter()