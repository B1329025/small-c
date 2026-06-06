/* 10_runtime_error.sc */
int main() {
    int x = 10;
    int bad_math = x / 0; // Intentional runtime error: division by zero
    
    printf("This line should never be printed\n");
    
    return 0;
}