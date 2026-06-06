/* 07_array_basics.sc */
int main() {
    int arr[5];
    int i;
    
    printf("--- Array Allocation Test ---
");
    
    for (i = 0; i < 5; i = i + 1) {
        arr[i] = i * 10;
    }
    
    printf("arr[3] = %d (Expected 30)\n", arr[3]);
    
    return 0;
}