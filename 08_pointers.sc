/* 08_pointers.sc */
void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

int main() {
    int x = 10;
    int y = 20;
    
    printf("--- Pointer Address and Dereference Test ---
");
    printf("Before swap: x = %d, y = %d\n", x, y);
    
    swap(&x, &y);
    
    printf("After swap: x = %d, y = %d (Expected x=20, y=10)\n", x, y);
    
    return 0;
}