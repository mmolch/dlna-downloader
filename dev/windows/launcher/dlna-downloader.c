#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "whereami.h"
#include <libgen.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define PZS_IMPLEMENTATION
#include "pzs_cat.h"

/** Windows char * to wchar_t conversion. */
wchar_t *nstrws_convert(const char *raw) {
    int size_needed = MultiByteToWideChar(CP_UTF8, 0, raw, -1, NULL, 0);
    wchar_t *rtn = (wchar_t *) calloc(1, size_needed * sizeof(wchar_t));
    MultiByteToWideChar(CP_UTF8, 0, raw, -1, rtn, size_needed);
    return rtn;
}

int Py_Main(int argc, wchar_t **argv);

int wmain(int argc, wchar_t const *argv[])
{
    int appDir_size = wai_getExecutablePath(NULL, 0, NULL)+1;
	char appDir[appDir_size];
	appDir[appDir_size-1] = '\0';
	wai_getExecutablePath(appDir, appDir_size, &appDir_size);
	
	char* bname = basename(appDir);
    *strrchr(bname, '.') = 0;

    dirname(appDir);

    int scriptPath_size = pzs_cat(NULL, appDir, "\\bin\\", bname, NULL);
    char scriptPath[scriptPath_size];
    pzs_cat((char*)&scriptPath, appDir, "\\bin\\", bname, NULL);

    if (argc <= 0) {
        return 0;
    }

    wchar_t *python_argv[argc+1];
    python_argv[0] = (wchar_t*)argv[0];
    python_argv[1] = nstrws_convert((char*)&scriptPath);

    for (int i=2; i<=argc; i++) {
        python_argv[i] = (wchar_t*)argv[i-1];
    }

    return Py_Main(argc+1, (wchar_t**)python_argv);
}
