#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "mapper_expr.h"
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); char line[512];
    while (fgets(line, sizeof line, f)) {
        line[strcspn(line, "\n")] = 0; if (!*line) continue;
        char *mode = strtok(line, "|"), *ex = strtok(NULL, "|"), *xs = strtok(NULL, "|");
        int inf = mode[0] == 'f', outf = (strlen(mode) == 2) ? mode[1] == 'f' : inf;
        mapper_expr e = mapper_expr_new_from_string(ex, inf, outf, 1);
        printf("%s|%s|", mode, ex);
        if (!e) { printf("PARSEFAIL\n"); continue; }
        for (char *t = strtok(xs, ","); t; t = strtok(NULL, ",")) {
            float fi = strtof(t, NULL), fo = 0; int ii = (int)strtol(t, NULL, 10), io = 0;
            mapper_expr_evaluate(e, inf ? (void*)&fi : (void*)&ii, outf ? (void*)&fo : (void*)&io);
            if (outf) printf("%.9g;", fo); else printf("%d;", io);
        }
        printf("\n"); mapper_expr_free(e);
    }
    return 0;
}
