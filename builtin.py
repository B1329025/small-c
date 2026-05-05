import math
import random
import sys
import memory  

class Builtins:
    def __init__(self):
        self.mapping = {
            'putchar':    self.putchar,
            'getchar':    self.getchar,
            'puts':       self.puts,
            'scanf':      self.scanf,
            'printf':     self.printf,
            'strlen':     self.strlen,
            'strcpy':     self.strcpy,
            'strcmp':     self.strcmp,
            'strcat':     self.strcat,
            'abs':        self.abs,
            'max':        self.max,
            'min':        self.min,
            'pow':        self.pow,
            'sqrt':       self.sqrt,
            'mod':        self.mod,
            'rand':       self.rand,
            'srand':      self.srand,
            'memset':     self.memset,
            'sizeof_int': self.sizeof_int,
            'sizeof_char':self.sizeof_char,
            'atoi':       self.atoi,
            'itoa':       self.itoa,
            'exit':       self.exit
        }

    # --- 輸入與輸出函式 ---
    def putchar(self, args):
        char_code = args[0]
        print(chr(char_code), end='', flush=True)
        return char_code

    def getchar(self, args):
        char = sys.stdin.read(1)
        return ord(char) if char else -1

    def puts(self, args):
        addr = args[0]
        s = ""
        while (c := memory.read(addr)) != 0:
            s += chr(c)
            addr += 1
        print(s)
        return 0

    def scanf(self, args):
        # 簡化版實作：僅支援 %d 與 %c
        fmt_addr = args[0]
        fmt = self._get_string(fmt_addr)
        placeholders = fmt.count('%')
        count = 0
        for i in range(placeholders):
            val = input().strip() # 互動式取得輸入
            target_addr = args[i + 1]
            try:
                # 根據規範，引數必須為指標
                memory.write(target_addr, int(val))
                count += 1
            except: break
        return count

    # --- 字串處理函式 ---
    def strlen(self, args):
        addr, length = args[0], 0
        while memory.read(addr + length) != 0:
            length += 1
        return length

    def strcpy(self, args):
        dest, src = args[0], args[1]
        i = 0
        while True:
            val = memory.read(src + i)
            memory.write(dest + i, val)
            if val == 0: break
            i += 1
        return dest

    def strcmp(self, args):
        s1_addr, s2_addr = args[0], args[1]
        i = 0
        while True:
            c1, c2 = memory.read(s1_addr + i), memory.read(s2_addr + i)
            if c1 != c2: return c1 - c2
            if c1 == 0: return 0
            i += 1

    def strcat(self, args):
        dest, src = args[0], args[1]
        d_idx = self.strlen([dest])
        s_idx = 0
        while True:
            val = memory.read(src + s_idx)
            memory.write(dest + d_idx + s_idx, val)
            if val == 0: break
            s_idx += 1
        return dest

    # --- 數學函式[cite: 31] ---
    def abs(self, args):
        return abs(args[0])

    def max(self, args):
        return max(args[0], args[1])

    def min(self, args):
        return min(args[0], args[1])

    def pow(self, args):
        base, exp = args[0], args[1]
        if exp < 0: return 0
        return int(math.pow(base, exp))

    def sqrt(self, args):
        if args[0] < 0:
            print("Runtime error: sqrt() argument must be non-negative.") # 規範要求
            return 0
        return int(math.sqrt(args[0]))

    def mod(self, args):
        if args[1] == 0:
            print("Runtime error: division by zero.") # 規範要求
            return 0
        return args[0] % args[1]

    def rand(self, args):
        return random.randint(0, 32767)

    def srand(self, args):
        random.seed(args[0])
        return 0

    # --- 記憶體與工具函式[cite: 31] ---
    def memset(self, args):
        ptr, value, size = args[0], args[1], args[2]
        for i in range(size):
            memory.write(ptr + i, value)
        return ptr

    def sizeof_int(self, args): return 4 # 固定為 4
    def sizeof_char(self, args): return 1 # 固定為 1

    def atoi(self, args):
        s = self._get_string(args[0])
        try: return int(s)
        except: return 0

    def itoa(self, args):
        val, addr = args[0], args[1]
        s = str(val)
        for i, char in enumerate(s):
            memory.write(addr + i, ord(char))
        memory.write(addr + len(s), 0) # 加上結尾空字元
        return 0

    def exit(self, args):
        sys.exit(args[0])

    # 內部輔助方法：從模擬記憶體讀取字串
    def _get_string(self, addr):
        chars = []
        while (c := memory.read(addr)) != 0:
            chars.append(chr(c))
            addr += 1
        return "".join(chars)
    def printf(self,fmt,arg_values):
        result = ""
        arg_idx = 0
        i = 0
        while i < len(fmt):
            if fmt[i] == '\\' and i + 1 < len(fmt) and fmt[i+1] == 'n':
                result += "\n"  # 將原始字串中的 \ 和 n 轉換為真正的換行符
                i += 2
            elif fmt[i] == '%' and i + 1 < len(fmt):
                specifier = fmt[i+1]
                if specifier == '%': # 輸出百分比符號本身
                    result += "%"
                    i += 2
                    continue
                
                if arg_idx >= len(arg_values):
                    raise RuntimeError("printf 格式字串與參數數量不符")
                val = arg_values[arg_idx]
                arg_idx += 1
                
                if specifier == 'd': # 整數
                    result += str(int(val))
                elif specifier == 'c': # 字元
                    result += chr(int(val))
                elif specifier == 'x': # 十六進位
                    result += hex(int(val))[2:]
                elif specifier == 's': # 字串 (假設 val 是記憶體位址)
                    addr = val
                    s_val = ""
                    # 模擬讀取直到遇到 \0
                    try:
                        while True:
                            # 讀取位址內容
                            char_code = memory.read(addr) 
                            
                            # 遇到結尾符 \0 則停止
                            if char_code == 0: 
                                break
                            
                            s_val += chr(char_code)
                            addr += 1
                            
                            # 安全機制：防止無限迴圈（可選）
                            if len(s_val) > 1000: 
                                break
                    except Exception:
                        raise RuntimeError(f"Runtime error: 讀取字串時記憶體存取越界 (位址: {addr})")
                    result += s_val
                else:
                    raise RuntimeError(f"printf 錯誤：不支援的佔位符 '%{specifier}'")
                i += 2 # 跳過 % 和佔位符
            else:
                result += fmt[i]
                i += 1
        if arg_idx < len(arg_values):
            raise RuntimeError(f"printf 錯誤：提供的參數 ({len(arg_values)}) 多於格式字串所需的數量 ({arg_idx})")
        print(result, end='', flush=True)
        return None