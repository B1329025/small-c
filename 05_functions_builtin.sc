/* 05_functions_builtin.sc */
void show_math(int val) {
    printf("abs(%d) = %d\n", val, abs(val));
}

int main() {
    printf("--- Built-in Function Integration Test ---
");
    show_math(-99);
    printf("pow(2, 5) = %d (Expected 32)\n", pow(2, 5));
    return 0;
}