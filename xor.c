#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// XOR decryption for the encrypted file using the key
// usage: ./xor <encrypted_file> <key> <output_file>
// thx github copilot

int main(int argc, char *argv[]) {
    FILE *fp, *fp2;
    char *key = argv[2];
    char *output_file = argv[3];
    char *encrypted_file = argv[1];
    char *buffer;
    char *buffer2;
    int i = 0;
    int j = 0;
    int key_length = strlen(key);
    int file_length = 0;
    int file_length2 = 0;
    int xor = 0;

    fp = fopen(encrypted_file, "r");
    fp2 = fopen(output_file, "w");

    if (fp == NULL) {
        printf("Error opening file\n");
        exit(1);
    }

    if (fp2 == NULL) {
        printf("Error opening file\n");
        exit(1);
    }

    // get file length
    fseek(fp, 0, SEEK_END);
    file_length = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    // allocate memory for buffer
    buffer = (char *)malloc(file_length * sizeof(char));
    buffer2 = (char *)malloc(file_length * sizeof(char));

    // read file into buffer
    fread(buffer, file_length, 1, fp);

    // XOR decryption
    for (i = 0; i < file_length; i++) {
        xor = buffer[i] ^ key[j];
        buffer2[i] = xor;
        j++;
        if (j == key_length) {
            j = 0;
        }
    }

    // write buffer to file
    fwrite(buffer2, file_length, 1, fp2);

    // free memory
    free(buffer);
    free(buffer2);

    // close files
    fclose(fp);
    fclose(fp2);

    return 0;
}