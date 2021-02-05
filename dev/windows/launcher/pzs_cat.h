/**************************************************************************************************
 *  File:    pzs_cat.h
 *  Purpose: Concatenate strings into a single, NUL terminated string
 *  Author:  Moritz Molch <mail@moritzmolch.de>
 *  Created: 02.01.2021
 *  License: Public Domain
 *************************************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#ifndef PZS_CAT_H
#define PZS_CAT_H

/**
 * @brief Concatenate strings into a single, NUL terminated string
 *
 * @example
 * int newString_size = pzs_cat(NULL, "One", "Two", "Three", NULL);
 * char newString[newString_size];
 * newString_size = pzs_cat((char*)&newString, "One", "Two", "Three", NULL);
 * if (newString_size < 0) {
 *     // ERROR
 * }
 * // newString: "OneTwoThree"
 *
 * @param outString destination buffer, set to NULL to only get the size
 *
 * @return the size of the resulting string (including a terminal NUL * character), -1 on error
 */
int pzs_cat(char *outString, ...);

#endif /* PZS_CAT_H */

/**************************************************************************************************
 * Implementation
 *************************************************************************************************/

#ifdef PZS_IMPLEMENTATION

#include <stdarg.h>
#include <string.h>

int pzs_cat(char *outString, ...)
{
    va_list args;
    char *arg = NULL;
    int outString_size = 1;

    va_start(args, outString);

    arg = va_arg(args, char*);
    while (arg != NULL) {
        size_t arg_length = strlen(arg);
        outString_size += arg_length;

        if (outString != NULL) {
            memcpy(outString, arg, arg_length);
            outString += arg_length;
        }

        arg = va_arg(args, char*);
    }
    va_end(args);

    if (outString != NULL) {
        outString[0] = '\0';
    }

    return outString_size;
}

#endif  /* PZS_IMPLEMENTATION */

#ifdef __cplusplus
}
#endif
