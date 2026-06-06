/* 02_variables.sc */
int x = 100; // Global variable

int main() {
    int x = 10; // Local variable (shadows global x)
    
    x += 5;
    
    printf("--- Variable Scope Test ---
");
    printf("Local x = %d (Expected 15)\n", x);
    
    return 0;
}