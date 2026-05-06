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
    user_code_buffer = []
    is_modified = False 
    
    # 支援多行輸入的關鍵變數
    pending_lines = [] 
    brace_level = 0 

    print("Small-C Interpreter (Enhanced Interactive Mode)")
    
    while True:
        try:
            # 根據大括號深度顯示提示字元，達成圖中的效果
            prompt = "sc> " if brace_level == 0 else ">   "
            line = input(prompt)
            
            if not line.strip() and brace_level == 0:
                continue

            # 統計大括號數量來判斷區塊是否結束
            brace_level += line.count('{')
            brace_level -= line.count('}')
            pending_lines.append(line)

            # 如果還在區塊內（大括號未閉合），繼續等待輸入
            if brace_level > 0:
                continue
            
            # 完整語句合併
            current_code = "\n".join(pending_lines)
            pending_lines = []
            
            # 檢查指令
            parts = current_code.strip().split()
            if not parts: continue
            cmd = parts[0].upper()

            # --- 系統指令 ---
            if cmd == "LOAD":
                if len(parts) < 2:
                    print("Usage: LOAD <filename>"); continue
                if is_modified:
                    confirm = input("Discard unsaved changes? (y/n): ")
                    if confirm.lower() != 'y': continue
                filename = parts[1]
                if os.path.exists(filename):
                    with open(filename, "r") as f:
                        user_code_buffer = f.read().splitlines()
                    is_modified = False
                    print(f"Loaded {len(user_code_buffer)} lines.")
                else:
                    print(f"Error: File '{filename}' not found.")

            elif cmd == "SAVE":
                if len(parts) < 2:
                    print("Usage: SAVE <filename>"); continue
                with open(parts[1], "w") as f:
                    f.write("\n".join(user_code_buffer))
                is_modified = False
                print(f"Saved {len(user_code_buffer)} lines.")

            elif cmd == "LIST":
                if not user_code_buffer:
                    print("Buffer is empty."); continue
                for i, content in enumerate(user_code_buffer, 1):
                    print(f"{i:3}: {content}")

            elif cmd == "NEW":
                evaluator.reset_state()
                user_code_buffer.clear()
                is_modified = False
                print("All cleared.")

            elif cmd == "RUN":
                if not user_code_buffer:
                    print("Buffer is empty."); continue
                execute_ast("\n".join(user_code_buffer), evaluator)

            elif cmd == "VARS":
                vars_info = evaluator.get_global_variables()
                print(f"{'Name':<10} {'Type':<10} {'Value'}")
                for name, info in vars_info.items():
                    print(f"{name:<10} {info['type']:<10} {info['value']}")

            elif cmd == "EXIT":
                sys.exit(0)

            # --- 即時執行模式 ---
            else:
                try:
                    lexer = Lexer(current_code)
                    parser = Parser(lexer.tokens)
                    nodes = parser.parse_program()
                    
                    for node in nodes:
                        # 在持續存在的作用域中執行，變數才能跨行維持
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

def execute_ast(code, evaluator):
    if not code.strip(): return
    lexer = Lexer(code)
    parser = Parser(lexer.tokens)
    ast_nodes = parser.parse_program()
    return evaluator.execute_top_level(ast_nodes)

if __name__ == "__main__":
    run_interactive_interpreter()