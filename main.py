import sys
import os
from lexar import Lexer
from parser import Parser
from evaluator import Evaluator
def validate_code(code):
    """
    實作 image_848134.jpg 要求的 CHECK 指令核心邏輯。
    進行語法檢查但不實際執行。
    """
    errors = []
    try:
        # 1. 詞法分析
        lexer = Lexer(code)
        tokens = lexer.tokens
        
        # 2. 語法分析
        parser = Parser(tokens)
        ast_nodes = parser.parse_program()
        
        # 3. 語意檢查 (選用：檢查 main 函式是否存在)
        has_main = any(
            node.get('type') == 'FunctionDecl' and node.get('name') == 'main' 
            for node in ast_nodes
        )
        if not has_main:
            errors.append({"line": "EOF", "msg": "Global Error: main() function is missing."})
            
    except Exception as e:
        # 捕捉 Parser 或 Lexer 拋出的具體錯誤
        # 假設您的錯誤訊息中包含 "Line X" 的字樣
        error_msg = str(e)
        line_num = "Unknown"
        if "line" in error_msg.lower():
            # 簡單解析錯誤訊息中的行號
            import re
            match = re.search(r'line\s*(\d+)', error_msg, re.I)
            if match:
                line_num = match.group(1)
        
        errors.append({"line": line_num, "msg": error_msg})
        
    return errors

def run_interactive_interpreter():
    evaluator = Evaluator()
    user_code_buffer = []
    # 用於追蹤緩衝區是否已修改且未儲存
    is_modified = False 

    print("Small-C Interpreter (Enhanced)")
    
    while True:
        try:
            line = input("sc> ")
            parts = line.strip().split()
            if not parts: continue
            cmd = parts[0].upper()

            # --- 3.1 程式管理指令 ---

            # LOAD <filename>: 從檔案載入程式
            if cmd == "LOAD":
                if len(parts) < 2:
                    print("Usage: LOAD <filename>"); continue
                
                # 檢查未儲存的修改
                if is_modified:
                    confirm = input("Current buffer is modified. Discard changes? (y/n): ")
                    if confirm.lower() != 'y': continue
                
                filename = parts[1]
                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        lines = f.read().splitlines()
                        user_code_buffer = lines
                    is_modified = False
                    print(f"Loaded {len(user_code_buffer)} lines.")
                else:
                    print(f"Error: File '{filename}' not found.")
            elif cmd =="ABOUT":
                print("niga ver 6.7.0")
            # SAVE <filename>: 儲存至檔案
            elif cmd == "SAVE":
                if len(parts) < 2:
                    print("Usage: SAVE <filename>"); continue
                try:
                    with open(parts[1], "w") as f:
                        f.write("\n".join(user_code_buffer))
                    is_modified = False
                    print(f"Saved {len(user_code_buffer)} lines.")
                except Exception as e:
                    print(f"Error saving file: {e}")

            # LIST / LIST <n> / LIST <n1>-<n2>
            elif cmd == "LIST":
                if not user_code_buffer:
                    print("Buffer is empty."); continue
                
                # 預設範圍
                start, end = 1, len(user_code_buffer)
                
                if len(parts) > 1:
                    if '-' in parts[1]: # 處理 n1-n2
                        n1, n2 = map(int, parts[1].split('-'))
                        start, end = n1, n2
                    else: # 處理單行 n
                        start = end = int(parts[1])
                
                for i in range(max(1, start), min(len(user_code_buffer), end) + 1):
                    print(f"{i:3}: {user_code_buffer[i-1]}")

            # EDIT <n>: 編輯第 n 行
            elif cmd == "EDIT":
                if len(parts) < 2:
                    print("Usage: EDIT <line_number>"); continue
                idx = int(parts[1]) - 1
                if 0 <= idx < len(user_code_buffer):
                    print(f"Old: {user_code_buffer[idx]}")
                    new_content = input(f"{idx+1}: ")
                    if new_content.strip(): # 若輸入為空則保留原行
                        user_code_buffer[idx] = new_content
                        is_modified = True
                else:
                    print("Error: Line number out of range.")

            # DELETE <n> / DELETE <n1>-<n2>
            elif cmd == "DELETE":
                if len(parts) < 2:
                    print("Usage: DELETE <line_number_or_range>"); continue
                
                if '-' in parts[1]:
                    n1, n2 = map(int, parts[1].split('-'))
                    # 由後往前刪除，避免索引偏移
                    for i in range(n2, n1 - 1, -1):
                        if 1 <= i <= len(user_code_buffer):
                            user_code_buffer.pop(i-1)
                else:
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(user_code_buffer):
                        user_code_buffer.pop(idx)
                is_modified = True

            # INSERT <n>: 在第 n 行前插入
            elif cmd == "INSERT":
                if len(parts) < 2:
                    print("Usage: INSERT <line_number>"); continue
                idx = int(parts[1]) - 1
                print("Enter code (type '.' on a single line to finish):")
                insert_idx = max(0, idx)
                while True:
                    code_line = input()
                    if code_line.strip() == ".": break
                    user_code_buffer.insert(insert_idx, code_line)
                    insert_idx += 1
                    is_modified = True

            # APPEND: 在末尾插入
            elif cmd == "APPEND":
                print("Enter code (type '.' on a single line to finish):")
                while True:
                    code_line = input()
                    if code_line.strip() == ".": break
                    user_code_buffer.append(code_line)
                    is_modified = True
            elif cmd == "CHECK":
                if not user_code_buffer:
                    print("Buffer is empty."); continue
                errors = validate_code("\n".join(user_code_buffer))
                if not errors:
                    print("No errors found.")
                else:
                    for err in errors:
                        print(f"Line {err['line']}: {err['msg']}")

            # TRACE ON / OFF: 執行追蹤模式
            elif cmd == "TRACE":
                if len(parts) > 1:
                    sub_cmd = parts[1].upper()
                    if sub_cmd == "ON":
                        trace_mode = True
                        print("Trace mode: ON")
                    elif sub_cmd == "OFF":
                        trace_mode = False
                        print("Trace mode: OFF")
                else:
                    print(f"Trace mode is currently {'ON' if trace_mode else 'OFF'}")

            # VARS: 顯示全域變數狀態
            elif cmd == "VARS":
                globals_dict = evaluator.get_global_variables()
                if not globals_dict:
                    print("No global variables defined."); continue
                
                print(f"{'Name':<10} {'Type':<10} {'Value'}")
                print("-" * 30)
                for name, info in globals_dict.items():
                    val_str = str(info['value'])
                    # 處理陣列與指標的特殊顯示
                    if info['is_array']:
                        elements = info['value'][:10]
                        val_str = f"[{', '.join(map(str, elements))}"
                        if len(info['value']) > 10: val_str += ", ..."
                        val_str += f"] (size: {len(info['value'])})"
                    elif info['is_pointer']:
                        val_str = f"{info['value']} (points to: {info['address']})"
                    
                    print(f"{name:<10} {info['type']:<10} {val_str}")

            # FUNCS: 列出定義的函數
            elif cmd == "FUNCS":
                funcs = evaluator.get_defined_functions()
                print(f"{'Function':<15} {'Return':<10} {'Params':<20} {'Line'}")
                print("-" * 55)
                for f in funcs:
                    line_info = "{built-in}" if f['is_builtin'] else f['line_num']
                    param_str = ", ".join([f"{p['type']} {p['name']}" for p in f['params']])
                    print(f"{f['name']:<15} {f['type']:<10} {param_str:<20} {line_info}")

            # NEW: 清除緩衝區並重置環境
            elif cmd == "NEW":
                if is_modified:
                    confirm = input("Current buffer is modified. Discard changes? (y/n): ")
                    if confirm.lower() != 'y': continue
                evaluator.reset_state()
                user_code_buffer.clear()
                is_modified = False
                print("Environment reset.")

            # RUN: 執行緩衝區程式
            elif cmd == "RUN":
                if not user_code_buffer:
                    print("Buffer is empty."); continue
                execute_ast("\n".join(user_code_buffer), evaluator)

            elif cmd == "EXIT":
                sys.exit(0)
            
            else:
                print(f"Unknown command: {cmd}")
            
        except Exception as e:
            print(f"Error: {e}")

def execute_ast(code, evaluator):

    if not code.strip(): return
    lexer = Lexer(code)
    parser = Parser(lexer.tokens)
    ast_nodes = parser.parse_program()
    result = evaluator.execute_top_level(ast_nodes)
    return result

if __name__ == "__main__":
    run_interactive_interpreter()