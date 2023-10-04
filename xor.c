#include <stdio.h>
#include <string.h> 

// XOR decryption for the encrypted file using the key
// usage: ./xor <encrypted_file> <key> <output_file>
// thx github copilot

long fsize(FILE *file) {
    long size;
    fseek(file, 0, SEEK_END);
    size = ftell(file);
    fseek(file, 0, SEEK_SET);
    return size;
}

int main(int argc, char *argv[]) {

    if (argc != 4) {
        printf("Usage: %s <encrypted_file> <key> <output_file>\n", argv[0]);
        return 1;
    }

    FILE *file = fopen(argv[1], "rb");
    FILE *output = fopen(argv[3], "wb");

    if (file == NULL) {
        printf("Error opening file %s\n", argv[1]);
        return 1;
    }

    char *key = argv[2];
    int key_len = strlen(key);
    int c;
    int i = 0;
    

    while ((c = fgetc(file)) != EOF) {
        fputc(c ^ key[i], output);
        i = (i + 1) % key_len;
    }

    fclose(file);
    fclose(output);
    return 0;
}