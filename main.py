import sys
import os
import re
from lexar import Lexer
from parser import Parser
from evaluator import Evaluator

def validate_code(code):
    """進行語法檢查但不實際執行"""
    errors = []
    try:
        lexer = Lexer(code)
        tokens = lexer.tokens
        parser = Parser(tokens)
        ast_nodes = parser.parse_program()
        
        has_main = any(
            hasattr(node, 'name') and node.name == 'main' 
            for node in ast_nodes
        )
        if not has_main:
            errors.append({"line": "EOF", "msg": "Global Error: main() function is missing."})
    except Exception as e:
        error_msg = str(e)
        line_num = "Unknown"
        match = re.search(r'line\s*(\d+)', error_msg, re.I)
        if match:
            line_num = match.group(1)
        errors.append({"line": line_num, "msg": error_msg})
    return errors

def run_interactive_interpreter():
    evaluator = Evaluator()
    user_code_buffer = []  # 程式緩衝區
    is_modified = False 
    trace_mode = False     # TRACE 開關
    
    pending_lines = [] 
    brace_level = 0 

    # 建立說明文件字典供 HELP <command> 使用
    help_docs = {
        "LOAD": "LOAD <filename>: 從指定檔案載入原始碼。會覆蓋目前緩衝區。",
        "SAVE": "SAVE <filename>: 將目前緩衝區內容儲存至檔案。",
        "LIST": "LIST [n|n1-n2]: 列出緩衝區內容。可指定行號或範圍。",
        "EDIT": "EDIT <n>: 編輯第 n 行內容。",
        "DELETE": "DELETE <n|n1-n2>: 刪除指定行或範圍。",
        "INSERT": "INSERT <n>: 在第 n 行前插入程式碼，輸入 '.' 結束。",
        "APPEND": "APPEND: 在緩衝區末尾增加程式碼，輸入 '.' 結束。",
        "NEW": "NEW: 清除緩衝區並重置解譯器狀態。",
        "RUN": "RUN: 執行目前緩衝區中的程式。",
        "CHECK": "CHECK: 進行語法檢查但不執行。",
        "TRACE": "TRACE <ON|OFF>: 開啟或關閉執行追蹤模式。",
        "VARS": "VARS: 顯示所有全域變數及其當前值。",
        "FUNCS": "FUNCS: 列出所有已定義的函式。",
        "CLEAR": "CLEAR: 清除終端機畫面。",
        "HELP": "HELP [command]: 顯示指令摘要或特定指令的詳細說明。",
        "EXIT": "EXIT 或 QUIT: 結束解譯器環境。"
    }

    print("Small-C Interactive Interpreter v3.0")
    print("System Software Final Project, Spring 2026")
    
    while True:
        try:
            # 根據大括號深度顯示提示字元
            prompt = "sc> " if brace_level == 0 else ">   "
            line = input(prompt)
            
            if not line.strip() and brace_level == 0:
                continue

            # 統計大括號數量判斷區塊
            brace_level += line.count('{')
            brace_level -= line.count('}')
            pending_lines.append(line)

            if brace_level > 0:
                continue
            
            current_code = "\n".join(pending_lines)
            pending_lines = []
            
            # 指令解析
            parts = current_code.strip().split()
            if not parts: continue
            cmd = parts[0].upper()

            # --- 3.1 程式管理指令 ---
            if cmd == "LOAD":
                if len(parts) < 2: print("Usage: LOAD <filename>"); continue
                if is_modified:
                    if input("Discard unsaved changes? (y/n): ").lower() != 'y': continue
                filename = parts[1]
                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        user_code_buffer = f.read().splitlines()
                    is_modified = False
                    print(f"Loaded {len(user_code_buffer)} lines.")
                else:
                    print(f"Error: File '{filename}' not found.")

            elif cmd == "SAVE":
                if len(parts) < 2: print("Usage: SAVE <filename>"); continue
                with open(parts[1], "w") as f:
                    f.write("\n".join(user_code_buffer))
                is_modified = False
                print(f"Saved {len(user_code_buffer)} lines.")

            elif cmd == "LIST":
                if not user_code_buffer: print("Buffer is empty."); continue
                start, end = 1, len(user_code_buffer)
                if len(parts) > 1:
                    if '-' in parts[1]: # 處理 LIST n1-n2
                        n1, n2 = map(int, parts[1].split('-'))
                        start, end = max(1, n1), min(len(user_code_buffer), n2)
                    else: # 處理 LIST n
                        start = end = int(parts[1])
                for i in range(start, end + 1):
                    print(f"{i:3}: {user_code_buffer[i-1]}")

            elif cmd == "EDIT":
                if len(parts) < 2: print("Usage: EDIT <n>"); continue
                idx = int(parts[1]) - 1
                if 0 <= idx < len(user_code_buffer):
                    print(f"{idx+1}: {user_code_buffer[idx]}")
                    new_line = input(f"{idx+1}: ")
                    if new_line.strip():
                        user_code_buffer[idx] = new_line
                        is_modified = True
                else: print("Line number out of range.")

            elif cmd == "DELETE":
                if len(parts) < 2: print("Usage: DELETE <n> or <n1-n2>"); continue
                if '-' in parts[1]:
                    n1, n2 = map(int, parts[1].split('-'))
                    del user_code_buffer[n1-1:n2]
                else:
                    user_code_buffer.pop(int(parts[1]) - 1)
                is_modified = True

            elif cmd == "INSERT":
                if len(parts) < 2: print("Usage: INSERT <n>"); continue
                idx = int(parts[1]) - 1
                print("Insert mode (type '.' to end):")
                temp_buffer = []
                while True:
                    text = input(f"{idx + len(temp_buffer) + 1}> ")
                    if text.strip() == ".": break
                    temp_buffer.append(text)
                user_code_buffer[idx:idx] = temp_buffer
                is_modified = True

            elif cmd == "APPEND":
                print("Append mode (type '.' to end):")
                while True:
                    text = input(f"{len(user_code_buffer) + 1}> ")
                    if text.strip() == ".": break
                    user_code_buffer.append(text)
                    is_modified = True

            elif cmd == "NEW":
                if is_modified:
                    if input("Discard changes? (y/n): ").lower() != 'y': continue
                evaluator.reset_state()
                user_code_buffer.clear()
                is_modified = False
                print("All cleared.")

            # --- 3.2 執行與除錯指令 ---
            elif cmd == "RUN":
                if not user_code_buffer: 
                    print("Buffer is empty.")
                    continue
                evaluator.reset_state() 
                
                try:
                    execute_ast("\n".join(user_code_buffer), evaluator) 
                except Exception as e:
                    print(f"Runtime Error: {e}")

            elif cmd == "CHECK":
                errors = validate_code("\n".join(user_code_buffer))
                if not errors: print("No errors found.")
                else:
                    for err in errors: print(f"Line {err['line']}: {err['msg']}")

            elif cmd == "TRACE":
                if len(parts) > 1 and parts[1].upper() == "ON":
                    trace_mode = True
                    print("Trace mode enabled.")
                else:
                    trace_mode = False
                    print("Trace mode disabled.")

            elif cmd == "VARS":
                vars_info = evaluator.get_global_variables()
                if not vars_info:
                    print("No global variables defined. (Note: VARS only shows global scope)")
                else:
                    print(f"{'Name':<10} {'Type':<10} {'Value'}")
                    for name, info in vars_info.items():
                        print(f"{name:<10} {info['type']:<10} {info['value']}")
            elif cmd == "FUNCS":
                # 直接在 main.py 實作，避免修改 evaluator.py 導致報錯
                if hasattr(evaluator, 'functions') and evaluator.functions:
                    print(f"{'Function Name':<20} {'Return Type':<15} {'Parameters'}")
                    print("-" * 50)
                    for f_name, f_node in evaluator.functions.items():
                        # 嘗試取得參數清單
                        params = "()"
                        if hasattr(f_node, 'params'):
                            p_list = []
                            for p in f_node.params:
                                # 根據你 Parser 的 Node 結構取得參數名稱與型別
                                p_type = getattr(p, 'type_name', 'int')
                                p_name = getattr(p, 'name', 'unknown')
                                p_list.append(f"{p_type} {p_name}")
                            params = f"({', '.join(p_list)})"
                        
                        ret_type = getattr(f_node, 'return_type', 'int')
                        print(f"{f_name:<20} {ret_type:<15} {params}")
                else:
                    print("No functions defined.")

            # --- 3.3 系統指令 (實作區) ---
            elif cmd == "HELP":
                if len(parts) > 1: # HELP <command>
                    target = parts[1].upper()
                    print(help_docs.get(target, f"Unknown command: {target}"))
                else: # HELP (摘要)
                    print("Available commands:")
                    print(", ".join(sorted(help_docs.keys())))
                    print("Type 'HELP <command>' for detailed info.")

            elif cmd == "CLEAR":
                # 執行系統清屏操作 (Windows: cls, Unix: clear)
                os.system('cls' if os.name == 'nt' else 'clear')

            elif cmd == "EXIT" or cmd == "QUIT":
                if is_modified:
                    if input("Unsaved changes! Exit anyway? (y/n): ").lower() != 'y': continue
                sys.exit(0)

            # --- 即時執行模式 ---
            else:
                try:
                    lexer = Lexer(current_code)
                    parser = Parser(lexer.tokens)
                    nodes = parser.parse_program()
                    for node in nodes:
                        evaluator.evaluate(node, evaluator.global_scope)
                    user_code_buffer.append(current_code)
                    is_modified = True
                except Exception as eval_e:
                    print(f"Error: {eval_e}")
            
        except KeyboardInterrupt:
            print("\nInterrupted.")
            pending_lines = []
            brace_level = 0
        except EOFError:
            break
        except Exception as e:
            print(f"Fatal Error: {e}")

def execute_ast(code, evaluator, trace=False):
    if not code.strip(): return
    lexer = Lexer(code)
    parser = Parser(lexer.tokens)
    ast_nodes = parser.parse_program()
    # 這裡若 trace 為 True，內部執行器應印出對應行號內容
    return evaluator.execute_top_level(ast_nodes)

if __name__ == "__main__":
    run_interactive_interpreter()