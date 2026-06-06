/* 03_if_logic.sc */
int main() {
    int a = 0;
    
    printf("--- Short-circuit Logic Test ---
");
    
    // Since 1 > 2 is false (0), the assignment (a = 1) must not be executed
    if ((1 > 2) && (a == 1)) {
        printf("This line should never be printed!\n");
    } else {
        printf("Short-circuit success! a = %d (Expected 0)\n", a);
    }
    
    return 0;
}