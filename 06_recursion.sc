/* 06_recursion.sc */
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    printf("--- Recursion Stack Test ---
");
    printf("5! = %d (Expected 120)\n", factorial(5));
    return 0;
}