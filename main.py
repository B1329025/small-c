import sys
import os
from lexar import Lexer
from parser import Parser
from evaluator import Evaluator

def run_interactive_interpreter():
    evaluator = Evaluator()
    user_code_buffer = []
    is_append_mode = False

    print("Small-C Interpreter (Enhanced)")
    
    while True:
        try:
            prompt = "> " if is_append_mode else "sc> "
            line = input(prompt)
            parts = line.strip().split()
            if not parts: continue
            cmd = parts[0].upper()

            # --- 系統指令 ---
            if cmd == "EXIT": sys.exit(0)
            elif cmd == "NEW":
                evaluator.reset_state()
                user_code_buffer.clear()
                is_append_mode = False
                print("Environment reset.")
            elif cmd == "APPEND": is_append_mode = True
            elif cmd == "RUN":
                execute_ast("\n".join(user_code_buffer), evaluator)
                is_append_mode = False
            elif cmd == "LIST":
                for i, c in enumerate(user_code_buffer): print(f"{i+1:3}: {c}")
            elif cmd == "SAVE":
                if len(parts) < 2: 
                    print("Usage: SAVE <filename>"); continue
                with open(parts[1], "w") as f:
                    f.write("\n".join(user_code_buffer))
                print(f"Saved to {parts[1]}")
            elif cmd == "LOAD":
                if len(parts) < 2: 
                    print("Usage: LOAD <filename>"); continue
                if os.path.exists(parts[1]):
                    with open(parts[1], "r") as f:
                        # 讀取後重置 buffer
                        user_code_buffer = f.read().splitlines()
                    print(f"Loaded {len(user_code_buffer)} lines.")
                else: print("Error: File not found.")
            elif cmd == "VARS":
                print("--- Global Variables ---")
                for name, info in evaluator.global_scope.symbols.items():
                    import memory
                    val = memory.read(info['address'])
                    print(f"{name}: {val} (at {info['address']})")
            elif cmd == "TRACE":
                evaluator.trace_enabled = not evaluator.trace_enabled
                print(f"Trace mode: {'ON' if evaluator.trace_enabled else 'OFF'}")
            elif cmd == "FUNCS":
                print("--- Defined Functions ---")
                if not evaluator.functions:
                    print("(No functions defined)")
                else:
                    for name, func_node in evaluator.functions.items():
                        line = getattr(func_node, 'lineno', 'Unknown')
                        params = ", ".join(func_node.params)
                        print(f"Function: {name}({params}) [Line: {line}]")
            elif cmd == "EDIT":
                if len(parts) < 2:
                    print("Usage: EDIT <line_number>"); continue
                try:
                    idx = int(parts[1]) - 1 # 轉為 0-based 索引
                    if 0 <= idx < len(user_code_buffer):
                        print(f"Old: {user_code_buffer[idx]}")
                        new_content = input(f"{idx+1}: ")
                        if new_content.strip():
                            user_code_buffer[idx] = new_content
                    else:
                        print("Error: Line number out of range.")
                except ValueError:
                    print("Error: Line number must be an integer.")
            else:
                if not is_append_mode:
                    user_code_buffer.append(line)
                    try:
                        execute_ast("\n".join(user_code_buffer), evaluator)
                    finally:
                        user_code_buffer.clear()
                else:
                    user_code_buffer.append(line)
            
        except Exception as e:
            print(f"Error: {e}")
            if not is_append_mode: user_code_buffer.clear()


def execute_ast(code, evaluator):

    if not code.strip(): return
    lexer = Lexer(code)
    parser = Parser(lexer.tokens)
    ast_nodes = parser.parse_program()
    result = evaluator.execute_top_level(ast_nodes)
    return result

if __name__ == "__main__":
    run_interactive_interpreter()