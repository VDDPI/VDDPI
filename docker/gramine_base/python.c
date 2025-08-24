/* Minimal main program -- everything is loaded from the library */

#include <stdio.h>
#include <stdlib.h>
#include <openssl/sha.h>
#include <string.h>

#include "Python.h"
#include <locale.h>

#define HASH_BUF_LEN 1024 * 16

#define DP_PROGRAM "./code/main.py"
#define DP_HASH_VALUE "dab72c36f4ca841c6bcad869684c7540bdb7b807f3dc5684bdf40619b3049fa1"

#define GEN_CERT_PROGRAM "gen_cert.py"
#define GCP_HASH_VALUE "ea68f815873ff35ef09049280a370b032e7f94e50be1c857e15c4124750754ef"

#ifdef __FreeBSD__
#include <fenv.h>
#endif

#ifdef MS_WINDOWS

int
wmain(int argc, wchar_t **argv)
{
    return Py_Main(argc, argv);
}
#else

int
main(int argc, char **argv)
{
    int verify_res;
    char *option_during_build[4][5] = {{"./python", "-E", "-S", "-m", "sysconfig"}, {"./python", "-E", "./setup.py", "build"}, {"./python", "-E", "./setup.py", "install"}, {"./python", "-E", "-m", "ensurepip"}};

    if ((!strncmp(argv[1], option_during_build[0][1], sizeof(option_during_build[0][1])) && !strncmp(argv[2], option_during_build[0][2], sizeof(option_during_build[0][2])) && !strncmp(argv[3], option_during_build[0][3], sizeof(option_during_build[0][3])) && !strncmp(argv[4], option_during_build[0][4], sizeof(option_during_build[0][4]))) ||
        ((!strncmp(argv[1], option_during_build[1][1], sizeof(option_during_build[1][1])) && !strncmp(argv[2], option_during_build[1][2], sizeof(option_during_build[1][2])) && !strncmp(argv[3], option_during_build[1][3], sizeof(option_during_build[1][3])))) ||
        ((!strncmp(argv[1], option_during_build[2][1], sizeof(option_during_build[2][1])) && !strncmp(argv[2], option_during_build[2][2], sizeof(option_during_build[2][2])) && !strncmp(argv[3], option_during_build[2][3], sizeof(option_during_build[2][3])))) || 
        ((!strncmp(argv[1], option_during_build[3][1], sizeof(option_during_build[3][1])) && !strncmp(argv[2], option_during_build[3][2], sizeof(option_during_build[3][2])) && !strncmp(argv[3], option_during_build[3][3], sizeof(option_during_build[3][3]))))) {
        return call_Py_Main(argc, argv);
    }
 
    if (!strncmp(argv[1], "-gencert", "8")) {
        FILE *fp;
        const char* fname = GEN_CERT_PROGRAM;

        fp = fopen(fname, "r");
        if (fp != NULL) {
            int fd;
            int i;
            unsigned char buf[HASH_BUF_LEN];
            unsigned char digest[SHA256_DIGEST_LENGTH];
            SHA256_CTX sha_ctx;
            const char *hash_value = GCP_HASH_VALUE;

            fd = fileno(fp);
            SHA256_Init(&sha_ctx);
            for (;;) {
                i = read(fd, buf, HASH_BUF_LEN);
                if (i <= 0)
                    break;
                SHA256_Update(&sha_ctx, buf, (unsigned long)i);
            }
            SHA256_Final(digest, &sha_ctx);

            for (int i = 0; i < sizeof(digest); ++i) {
                char *tmp = malloc(sizeof(char) * 3);
                sprintf(tmp, "%02x", digest[i]);
                if (!(tmp[0] == hash_value[i * 2] && tmp[1] == hash_value[i * 2 + 1])) {
                    printf("-----------------------------------------------------------------------------------------------------------------------\n");
                    printf("Verification of hash value failed.\n");
                    printf("%s is not an appropriate certificate issuance program.\n", GEN_CERT_PROGRAM);
                    printf("-----------------------------------------------------------------------------------------------------------------------\n");
                    return 1;
                }
                free(tmp);
            }
            printf("-----------------------------------------------------------------------------------------------------------------------\n");
            printf("Successfully verified the hash value of the certificate issuing program!\n");
            printf("sha256(%s): %s\n", GEN_CERT_PROGRAM, GCP_HASH_VALUE);
            printf("-----------------------------------------------------------------------------------------------------------------------\n");
            fclose(fp);
        }

        const int GC_PROGRAM_ARGC = 2;
        char *gen_cert_argv[GC_PROGRAM_ARGC];
        
        // [0] ./python [1] ./gen_cert.py
        gen_cert_argv[0] = argv[0];
        gen_cert_argv[1] = GEN_CERT_PROGRAM;
        // gen_cert_argv[2] = argv[2];
        // gen, mail_cert_argv[3] = argv[3];
        return call_Py_Main(GC_PROGRAM_ARGC, gen_cert_argv);
    } else {
        FILE *fp;
        const char* fname = DP_PROGRAM;

        fp = fopen(fname, "r");
        if (fp != NULL) {
            int fd;
            int i;
            unsigned char buf[HASH_BUF_LEN];
            unsigned char digest[SHA256_DIGEST_LENGTH];
            SHA256_CTX sha_ctx;
            const char *hash_value = DP_HASH_VALUE;

            fd = fileno(fp);
            SHA256_Init(&sha_ctx);
            for (;;) {
                i = read(fd, buf, HASH_BUF_LEN);
                if (i <= 0)
                    break;
                SHA256_Update(&sha_ctx, buf, (unsigned long)i);
            }
            SHA256_Final(digest, &sha_ctx);

            for (int i = 0; i < sizeof(digest); ++i) {
                char *tmp = malloc(sizeof(char) * 3);
                sprintf(tmp, "%02x", digest[i]);
                if (!(tmp[0] == hash_value[i * 2] && tmp[1] == hash_value[i * 2 + 1])) {
                    printf("-----------------------------------------------------------------------------------------------------------------------\n");
                    printf("Verification of hash value failed.\n");
                    printf("%s is not an appropriate data processing program.\n", DP_PROGRAM);
                    printf("-----------------------------------------------------------------------------------------------------------------------\n");
                    return 1;
                }
                free(tmp);
            }
            printf("-----------------------------------------------------------------------------------------------------------------------\n");
            printf("Successfully verified the hash value of the data processing program!\n");
            printf("sha256(%s): %s\n", DP_PROGRAM, DP_HASH_VALUE);
            printf("-----------------------------------------------------------------------------------------------------------------------\n");
            fclose(fp);
        }
        
        return call_Py_Main(argc, argv);
    }
}
#endif

int call_Py_Main(int argc, char **argv) {

    wchar_t **argv_copy;
    /* We need a second copy, as Python might modify the first one. */
    wchar_t **argv_copy2;
    int i, res;
    char *oldloc;

    /* Force malloc() allocator to bootstrap Python */
    (void)_PyMem_SetupAllocators("malloc");

    argv_copy = (wchar_t **)PyMem_RawMalloc(sizeof(wchar_t*) * (argc+1));
    argv_copy2 = (wchar_t **)PyMem_RawMalloc(sizeof(wchar_t*) * (argc+1));
    if (!argv_copy || !argv_copy2) {
        fprintf(stderr, "out of memory\n");
        return 1;
    }
    /* 754 requires that FP exceptions run in "no stop" mode by default,
     * and until C vendors implement C99's ways to control FP exceptions,
     * Python requires non-stop mode.  Alas, some platforms enable FP
     * exceptions by default.  Here we disable them.
     */
#ifdef __FreeBSD__
    fedisableexcept(FE_OVERFLOW);
#endif

    oldloc = _PyMem_RawStrdup(setlocale(LC_ALL, NULL));
    if (!oldloc) {
        fprintf(stderr, "out of memory\n");
        return 1;
    }

    setlocale(LC_ALL, "");
    for (i = 0; i < argc; i++) {
        argv_copy[i] = Py_DecodeLocale(argv[i], NULL);
        if (!argv_copy[i]) {
            PyMem_RawFree(oldloc);
            fprintf(stderr, "Fatal Python error: "
                            "unable to decode the command line argument #%i\n",
                            i + 1);
            return 1;
        }
        argv_copy2[i] = argv_copy[i];
    }

    argv_copy2[argc] = argv_copy[argc] = NULL;

    setlocale(LC_ALL, oldloc);
    PyMem_RawFree(oldloc);

    
    res = Py_Main(argc, argv_copy);

    /* Force again malloc() allocator to release memory blocks allocated
       before Py_Main() */
    (void)_PyMem_SetupAllocators("malloc");

    for (i = 0; i < argc; i++) {
        PyMem_RawFree(argv_copy2[i]);
    }
    PyMem_RawFree(argv_copy);
    PyMem_RawFree(argv_copy2);

    return res;
}
