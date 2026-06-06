/* 04_loops.sc */
int main() {
    int i;
    int sum = 0;
    
    printf("--- Loop and Jump Test ---
");
    
    for (i = 1; i <= 10; i = i + 1) {
        if (i == 5) continue; // Skip 5
        if (i > 8) break;     // Terminate when i > 8
        sum += i;
    }
    
    // Calculation: 1 + 2 + 3 + 4 + 6 + 7 + 8 = 31
    printf("Sum = %d (Expected 31)\n", sum);
    
    return 0;
}