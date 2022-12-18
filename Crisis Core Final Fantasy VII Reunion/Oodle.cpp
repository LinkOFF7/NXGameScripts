/* Program was made for FF7 Crisis Core Reunion usage. 
Add this code to Visual Studio project, download Unreal Engine 4.27+ (not tested with 5),
link project with UnrealPak OodleData plugin sdk header folder and lib file (tested sdk version: 2.9.0),
and compile. It's forcing Mermaid compression method because it's used by Crisis Core ucas files*/

#define OODLE_ALLOW_DEPRECATED_COMPRESSORS

#include <iostream>
#include <fcntl.h>
#include <io.h>
#include "oodle2.h"

int printUsage() {
    std::cerr << ".exe [option] file_path/stdin=%d output_file_path/stdout\n";
    std::cerr << "Option:\n";
    std::cerr << "-c %d: compress file using Mermaid, %d compression level (from -4 to 9)\n";
    std::cerr << "-d %d: decompress file, %d exact decompressed file size (0 is not accepted, wrong value will return error)\n";
    std::cerr << "Other:\n";
    std::cerr << "file_path/stdin=%d: you can either provide input file path, or use stdin by writing \"stdin=%d\", where %d is size of stdin binary data\n";
    std::cerr << "output_file_path/stdout: you can either provide input file path, or use stdout by writing \"stdout\"";
    return 1;
}

int main(int argc, char* argv[])
{
    long compression_level = 9;
    bool compress = false;
    char* p = 0;
    long decompress_size = 0;

    if (argc != 5) {
        return printUsage();
    }

    if (!strncmp(argv[1], "-c", 2)) {
        errno = 0;
        compress = true;
        compression_level = strtol(argv[2], &p, 10);
        if (errno != 0 || *p != '\0' || compression_level > 9 || compression_level < -4) {
            std::cerr << "Wrong compression level input!\n";
            return printUsage();
        }
    }
    else if (strncmp(argv[1], "-d", 2)) {
        std::cerr << "Wrong option!";
        return printUsage();
    }
    else {
        errno = 0;
        decompress_size = strtol(argv[2], &p, 10);
        if (errno != 0 || *p != '\0' || decompress_size > INT_MAX || decompress_size < 1) {
            std::cerr << "Wrong decompress size input!\n";
            return printUsage();
        }
    }

    FILE* file = 0;
    size_t filesize = 0;
    void* buffer = 0;

    if (!strncmp(argv[3], "stdin", 5)) {
        filesize = strtol(argv[3] + 6, &p, 10);
        buffer = malloc(filesize);
        _setmode(_fileno(stdin), _O_BINARY);
        fread(buffer, filesize, 1, stdin);
    }
    else {
        fopen_s(&file, argv[3], "rb");
        fseek(file, 0, 2);
        filesize = ftell(file);
        fseek(file, 0, 0);
        buffer = malloc(filesize);
        fread(buffer, filesize, 1, file);
        fclose(file);
    }

    if (!compress) {
        void* new_buffer = malloc(decompress_size);
        size_t dec_size = OodleLZ_Decompress(buffer, filesize, new_buffer, decompress_size, OodleLZ_FuzzSafe_Yes, OodleLZ_CheckCRC_No, OodleLZ_Verbosity_Lots);
        if (!dec_size) {
            std::cerr << "Error while decompressing! Possible that provided decompression size is wrong.\n";
            return printUsage();
        }
        if (!strncmp(argv[4], "stdout", 6) && new_buffer) {
            fflush(stdout);
            _setmode(_fileno(stdout), _O_BINARY);
            fwrite(new_buffer, decompress_size, 1, stdout);
        }
        else {
            FILE* newfile;
            fopen_s(&newfile, argv[4], "wb");
            if (newfile && new_buffer) {
                fwrite(new_buffer, decompress_size, 1, newfile);
                fclose(newfile);
            }
            free(new_buffer);
            std::cout << dec_size << "\n";
        }
        return 0;
    }
    else {
        size_t comp_buffer_size = OodleLZ_GetCompressedBufferSizeNeeded(OodleLZ_Compressor_Mermaid, filesize);
        void* comp_buffer = malloc(comp_buffer_size);
        size_t com_size = OodleLZ_Compress(OodleLZ_Compressor_Mermaid, buffer, filesize, comp_buffer, OodleLZ_CompressionLevel(compression_level));
        if (!com_size) {
            std::cerr << "Error while compressing!\n";
            return 1;
        }
        if (!strncmp(argv[4], "stdout", 6)) {
            fflush(stdout);
            _setmode(_fileno(stdout), _O_BINARY);
            fwrite(comp_buffer, com_size, 1, stdout);
        }
        else {
            FILE* newfile;
            fopen_s(&newfile, argv[4], "wb");
            fwrite(comp_buffer, com_size, 1, newfile);
            fclose(newfile);
            free(comp_buffer);
            std::cout << com_size << "\n";
        }
        return 0;
    }
}
