/* 01_arithmetic.sc */
int main() {
    int a = -5 + 3 * 4;       
    int b = 100 % 7;          
    int c = (10 << 2) | 3;    
    
    printf("--- testing ---\n");
    printf("a = %d (Expected 7)\n", a);
    printf("b = %d (Expected 2)\n", b);
    printf("c = %d (Expected 43)\n", c);
    
    return 0;
}