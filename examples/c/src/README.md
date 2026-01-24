# Most usefull commands:

## gcc
gcc -fdump-tree-all-raw-lineno   -fdump-rtl-all-raw-lineno -o main.exe main.c


## clang

### ast dump

 `clang -Xclang -ast-dump -fsyntax-only main.c > ast-dump.ast`
or 
 `clang -Xclang -ast-dump -fsyntax-only main.c > ast-dump.ast`
### preprocessing dump

`pp-trace main.c > pptrace.ast` 

contains all preprocessing directives and all usages.