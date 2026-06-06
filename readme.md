Small-C Interactive Interpreter v3.0  

 

System Software Final Project, Spring 2026 開發團隊：彭文璨、陳恩立、謝熙睿  

 

專案概述 (Project Overview)  

 

本專題實作了一個 Small-C 語言的互動式解譯器 (Interactive Interpreter)。Small-C 為標準 C 語言 (ISO C) 的嚴格子集。有別於傳統的批次編譯器 (Batch Compiler)，本系統提供了一個類似 REPL (Read-Eval-Print Loop) 的操作環境。使用者可在命令提示符下進行逐行原始碼編寫、即時語法解析、以及動態執行，同時支援透過內建指令載入完整的原始碼檔案進行除錯與執行。  

 

本系統的設計高度整合了系統軟體核心技術，包含語彙分析 (Lexical Analysis)、遞迴下降語法分析 (Recursive Descent Parsing)、抽象語法樹 (Abstract Syntax Tree, AST) 建構、符號表 (Symbol Table) 管理與虛擬執行期環境 (Runtime Environment) 的記憶體模擬。  

 

  

 

環境需求與啟動 (Prerequisites & Usage)  

 

系統需求  

 

直譯器：Python 3 (建議版本 3.10 或以上)。  

 

相依套件：本專案採用純 Python 標準函式庫開發，無需安裝額外的第三方套件。  

 

啟動指令  

 

請於終端機中導覽至專案根目錄，並執行以下指令啟動互動式解譯器：  

 

python main.py  

 

成功啟動後，系統將顯示歡迎訊息，並進入帶有 sc> 提示字元的互動模式。  

 

  

 

支援的語言特性 (Language Features)  

 

本系統支援 Small-C 規範中的核心功能：  

 

資料型別 (Data Types)：支援 32 位元有號整數 int、8 位元有號字元 char。支援一維陣列 (Array) 與單層指標 (int*, char*) 宣告，並能在內部以模擬位址進行精確的指標算術運算。  

 

控制結構 (Control Structures)：完整支援 if/else、while、for、do/while 迭代結構，以及 break、continue 與 return 流程控制語句。  

 

運算子與表達式 (Operators & Expressions)：支援基礎算術、關係比較、位元運算、複合指派，以及具備短路求值 (Short-circuit evaluation) 特性的邏輯運算 (&&, ||)。  

 

函式支援 (Functions)：支援全域函式定義、傳值呼叫 (Call by value)、遞迴呼叫 (Recursive calls)。  

 

標準內建函式庫 (Built-in Library)：系統內建實作了多種標準 C 函式，包含 I/O (printf, scanf, putchar, getchar)、字串處理 (strlen, strcpy, strcmp, strcat)、數學運算 (abs, sqrt, pow, rand) 與記憶體操作 (memset)。  

 

  

 

系統架構與模組設計 (System Architecture)  

 

系統採用模組化設計，各階段職責明確：  

 

lexar.py (語彙分析器): 利用正規表達式 (Regular Expressions) 將原始碼字串轉換為 Token 序列，並實作了初步的前處理器巨集 (如 #define 常數替換)。  

 

parser.py (語法分析器): 實作遞迴下降解析器 (Recursive Descent Parser)，將 Token 序列轉換為抽象語法樹 (AST)，並負責語法錯誤的偵測與行號綁定。  

 

nodes.py (AST 節點定義): 定義了構成抽象語法樹的各類節點資料結構。  

 

evaluator.py (語意分析與執行引擎): 採用 Tree-walking Interpreter 架構遍歷 AST。負責作用域 (Scope) 管理、函式呼叫堆疊 (Call Stack) 維護，以及各類節點的求值與執行。  

 

memory.py (虛擬記憶體管理): 以一維陣列模擬真實機器的記憶體空間，負責變數的定址、陣列連續空間分配與記憶體讀寫操作，為指標運算提供底層支援。  

 

builtin.py (內建函式實作): 作為系統的外部介面，將 Small-C 呼叫橋接至 Python 的底層實作。  

 

  

 

互動環境指令集 (REPL Commands)  

 

在 sc> 提示字元下，系統提供以下環境指令進行程式碼管理與除錯操作：  

 

程式與緩衝區管理  

 

LOAD ：從外部檔案載入 Small-C 原始碼至緩衝區。  

 

SAVE ：將緩衝區內的原始碼寫入至外部檔案。  

 

LIST [n | n1-n2]：列出緩衝區原始碼，可指定特定行號或區間。  

 

EDIT ：修改緩衝區中第 n 行的程式碼。  

 

INSERT / APPEND：進入插入模式，於指定行或末尾新增程式碼，輸入 . 結束。  

 

DELETE <n | n1-n2>：刪除指定範圍的程式碼。  

 

NEW：清空緩衝區並重置解譯器之執行狀態 (包含符號表與記憶體)。  

 

執行與狀態除錯  

 

RUN：解析並執行目前緩衝區的程式碼。  

 

CHECK：執行語法與靜態語意檢查，回報潛在錯誤但不執行。  

 

TRACE <ON/OFF>：開關追蹤模式。開啟時將於終端機顯示正在執行的程式碼行號與敘述。  

 

VARS：輸出當前全域符號表，顯示變數的型別、虛擬位址與當前記憶體數值。  

 

FUNCS：列出系統目前已註冊之所有自定義與內建函式列表 (含參數與回傳型別)。  

 

系統控制  

 

CLEAR：清除終端機畫面。  

 

HELP [command]：顯示指令摘要或特定指令的詳細說明。  

 

ABOUT：顯示解譯器版本資訊與作者資料。  

 

EXIT / QUIT：安全結束解譯器執行環境。  

 

  

 

版權聲明：本專案依據 MIT License 授權釋出。  
