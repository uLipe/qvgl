#ifndef QVGL_TEST_H
#define QVGL_TEST_H

#include <stdio.h>
#include <stdlib.h>

static int qvgl_test_failures;

#define QVGL_ASSERT(cond) do { \
        if(!(cond)) { \
            fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
            qvgl_test_failures++; \
        } \
    } while(0)

#define QVGL_TEST_RUN(fn) do { \
        qvgl_test_failures = 0; \
        fn(); \
        if(qvgl_test_failures != 0) return EXIT_FAILURE; \
    } while(0)

#endif
