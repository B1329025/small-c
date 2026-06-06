/* 12_fibonacci.sc */
int fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int i;
    printf("Fibonacci sequence:\n");
    for (i = 0; i < 10; i = i + 1) {
        printf("F(%d) = %d\n", i, fibonacci(i));
    }
    return 0;
}