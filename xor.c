#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// XOR decryption for the encrypted file using the key
// usage: ./xor <encrypted_file> <key> <output_file>
// thx github copilot

int main(int argc, char *argv[]) {
    FILE *file = fopen(argv[1], "rb");
    FILE *output = fopen(argv[3], "wb");
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

