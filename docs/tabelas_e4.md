# E4 - Analisador Sintatico Preditivo Tabular

Este documento registra a gramatica usada pelo analisador sintatico tabular
implementado em `src/compilador.py`, suas tabelas FIRST/FOLLOW e a tabela
parser LL(1). A numeracao das producoes segue a gramatica do PDF base do
trabalho.

## Gramatica

```text
1  PROGRAM            -> FUNCTION_LIST
2  FUNCTION_LIST      -> FUNCTION FUNCTION_LIST_TAIL
3  FUNCTION_LIST_TAIL -> FUNCTION FUNCTION_LIST_TAIL
4  FUNCTION_LIST_TAIL -> epsilon
5  FUNCTION           -> TYPE id ( PARAM_LIST_OPT ) BLOCK
6  PARAM_LIST_OPT     -> PARAM_LIST
7  PARAM_LIST_OPT     -> epsilon
8  PARAM_LIST         -> PARAM PARAM_LIST_TAIL
9  PARAM_LIST_TAIL    -> , PARAM PARAM_LIST_TAIL
10 PARAM_LIST_TAIL    -> epsilon
11 PARAM              -> TYPE id
12 BLOCK              -> { DECL_LIST_OPT STMT_LIST_OPT }
13 DECL_LIST_OPT      -> DECL_LIST
14 DECL_LIST_OPT      -> epsilon
15 DECL_LIST          -> VAR_DECL DECL_LIST_TAIL
16 DECL_LIST_TAIL     -> VAR_DECL DECL_LIST_TAIL
17 DECL_LIST_TAIL     -> epsilon
18 VAR_DECL           -> TYPE id ;
19 STMT_LIST_OPT      -> STMT_LIST
20 STMT_LIST_OPT      -> epsilon
21 STMT_LIST          -> STMT STMT_LIST_TAIL
22 STMT_LIST_TAIL     -> STMT STMT_LIST_TAIL
23 STMT_LIST_TAIL     -> epsilon
24 STMT               -> ASSIGN_STMT
25 STMT               -> IF_STMT
26 STMT               -> WHILE_STMT
27 STMT               -> PRINT_STMT
28 STMT               -> RETURN_STMT
29 STMT               -> BLOCK
30 ASSIGN_STMT        -> id = EXPR ;
31 RETURN_STMT        -> return EXPR ;
32 PRINT_STMT         -> print ( EXPR ) ;
33 IF_STMT            -> if ( EXPR ) STMT ELSE_PART
34 ELSE_PART          -> else STMT
35 ELSE_PART          -> epsilon
36 WHILE_STMT         -> while ( EXPR ) STMT
37 EXPR               -> REL_EXPR
38 REL_EXPR           -> ADD_EXPR REL_EXPR_TAIL
39 REL_EXPR_TAIL      -> REL_OP ADD_EXPR
40 REL_EXPR_TAIL      -> epsilon
41 REL_OP             -> ==
42 REL_OP             -> !=
43 REL_OP             -> <
44 REL_OP             -> >
45 REL_OP             -> <=
46 REL_OP             -> >=
47 ADD_EXPR           -> MUL_EXPR ADD_EXPR_TAIL
48 ADD_EXPR_TAIL      -> + MUL_EXPR ADD_EXPR_TAIL
49 ADD_EXPR_TAIL      -> - MUL_EXPR ADD_EXPR_TAIL
50 ADD_EXPR_TAIL      -> epsilon
51 MUL_EXPR           -> FACTOR MUL_EXPR_TAIL
52 MUL_EXPR_TAIL      -> * FACTOR MUL_EXPR_TAIL
53 MUL_EXPR_TAIL      -> / FACTOR MUL_EXPR_TAIL
54 MUL_EXPR_TAIL      -> epsilon
55 FACTOR             -> ( EXPR )
56 FACTOR             -> id FACTOR_TAIL
57 FACTOR             -> num
58 FACTOR_TAIL        -> ( ARG_LIST_OPT )
59 FACTOR_TAIL        -> epsilon
60 ARG_LIST_OPT       -> ARG_LIST
61 ARG_LIST_OPT       -> epsilon
62 ARG_LIST           -> EXPR ARG_LIST_TAIL
63 ARG_LIST_TAIL      -> , EXPR ARG_LIST_TAIL
64 ARG_LIST_TAIL      -> epsilon
65 TYPE               -> int
66 TYPE               -> float
```

## FIRST

```text
PROGRAM:            int, float
FUNCTION_LIST:      int, float
FUNCTION_LIST_TAIL: int, float, epsilon
FUNCTION:           int, float
PARAM_LIST_OPT:     int, float, epsilon
PARAM_LIST:         int, float
PARAM_LIST_TAIL:    ,, epsilon
PARAM:              int, float
BLOCK:              {
DECL_LIST_OPT:      int, float, epsilon
DECL_LIST:          int, float
DECL_LIST_TAIL:     int, float, epsilon
VAR_DECL:           int, float
STMT_LIST_OPT:      id, if, while, print, return, {, epsilon
STMT_LIST:          id, if, while, print, return, {
STMT_LIST_TAIL:     id, if, while, print, return, {, epsilon
STMT:               id, if, while, print, return, {
ASSIGN_STMT:        id
RETURN_STMT:        return
PRINT_STMT:         print
IF_STMT:            if
ELSE_PART:          else, epsilon
WHILE_STMT:         while
EXPR:               (, id, num
REL_EXPR:           (, id, num
REL_EXPR_TAIL:      ==, !=, <, >, <=, >=, epsilon
REL_OP:             ==, !=, <, >, <=, >=
ADD_EXPR:           (, id, num
ADD_EXPR_TAIL:      +, -, epsilon
MUL_EXPR:           (, id, num
MUL_EXPR_TAIL:      *, /, epsilon
FACTOR:             (, id, num
FACTOR_TAIL:        (, epsilon
ARG_LIST_OPT:       (, id, num, epsilon
ARG_LIST:           (, id, num
ARG_LIST_TAIL:      ,, epsilon
TYPE:               int, float
```

## FOLLOW

```text
PROGRAM:            $
FUNCTION_LIST:      $
FUNCTION_LIST_TAIL: $
FUNCTION:           int, float, $
PARAM_LIST_OPT:     )
PARAM_LIST:         )
PARAM_LIST_TAIL:    )
PARAM:              ,, )
BLOCK:              id, if, while, print, return, {, }, int, float, else, $
DECL_LIST_OPT:      id, if, while, print, return, {, }
DECL_LIST:          id, if, while, print, return, {, }
DECL_LIST_TAIL:     id, if, while, print, return, {, }
VAR_DECL:           int, float, id, if, while, print, return, {, }
STMT_LIST_OPT:      }
STMT_LIST:          }
STMT_LIST_TAIL:     }
STMT:               id, if, while, print, return, {, }, else
ASSIGN_STMT:        id, if, while, print, return, {, }, else
RETURN_STMT:        id, if, while, print, return, {, }, else
PRINT_STMT:         id, if, while, print, return, {, }, else
IF_STMT:            id, if, while, print, return, {, }, else
ELSE_PART:          id, if, while, print, return, {, }, else
WHILE_STMT:         id, if, while, print, return, {, }, else
EXPR:               ), ;, ,
REL_EXPR:           ), ;, ,
REL_EXPR_TAIL:      ), ;, ,
REL_OP:             (, id, num
ADD_EXPR:           ==, !=, <, >, <=, >=, ), ;, ,
ADD_EXPR_TAIL:      ==, !=, <, >, <=, >=, ), ;, ,
MUL_EXPR:           +, -, ==, !=, <, >, <=, >=, ), ;, ,
MUL_EXPR_TAIL:      +, -, ==, !=, <, >, <=, >=, ), ;, ,
FACTOR:             *, /, +, -, ==, !=, <, >, <=, >=, ), ;, ,
FACTOR_TAIL:        *, /, +, -, ==, !=, <, >, <=, >=, ), ;, ,
ARG_LIST_OPT:       )
ARG_LIST:           )
ARG_LIST_TAIL:      )
TYPE:               id
```

## Tabela Parser LL(1)

As entradas da tabela indicam o numero da producao usada.

```text
M(PROGRAM, int/float) = 1
M(FUNCTION_LIST, int/float) = 2
M(FUNCTION_LIST_TAIL, int/float) = 3
M(FUNCTION_LIST_TAIL, $) = 4
M(FUNCTION, int/float) = 5
M(PARAM_LIST_OPT, int/float) = 6
M(PARAM_LIST_OPT, )) = 7
M(PARAM_LIST, int/float) = 8
M(PARAM_LIST_TAIL, ,) = 9
M(PARAM_LIST_TAIL, )) = 10
M(PARAM, int/float) = 11
M(BLOCK, {) = 12
M(DECL_LIST_OPT, int/float) = 13
M(DECL_LIST_OPT, id/if/while/print/return/{/}) = 14
M(DECL_LIST, int/float) = 15
M(DECL_LIST_TAIL, int/float) = 16
M(DECL_LIST_TAIL, id/if/while/print/return/{/}) = 17
M(VAR_DECL, int/float) = 18
M(STMT_LIST_OPT, id/if/while/print/return/{) = 19
M(STMT_LIST_OPT, }) = 20
M(STMT_LIST, id/if/while/print/return/{) = 21
M(STMT_LIST_TAIL, id/if/while/print/return/{) = 22
M(STMT_LIST_TAIL, }) = 23
M(STMT, id) = 24
M(STMT, if) = 25
M(STMT, while) = 26
M(STMT, print) = 27
M(STMT, return) = 28
M(STMT, {) = 29
M(ASSIGN_STMT, id) = 30
M(RETURN_STMT, return) = 31
M(PRINT_STMT, print) = 32
M(IF_STMT, if) = 33
M(ELSE_PART, else) = 34
M(ELSE_PART, id/if/while/print/return/{/}/$) = 35
M(WHILE_STMT, while) = 36
M(EXPR, (/id/num) = 37
M(REL_EXPR, (/id/num) = 38
M(REL_EXPR_TAIL, ==/!=/</>/<=/>=) = 39
M(REL_EXPR_TAIL, )/;/,) = 40
M(REL_OP, ==) = 41
M(REL_OP, !=) = 42
M(REL_OP, <) = 43
M(REL_OP, >) = 44
M(REL_OP, <=) = 45
M(REL_OP, >=) = 46
M(ADD_EXPR, (/id/num) = 47
M(ADD_EXPR_TAIL, +) = 48
M(ADD_EXPR_TAIL, -) = 49
M(ADD_EXPR_TAIL, ==/!=/</>/<=/>=/)/;/,) = 50
M(MUL_EXPR, (/id/num) = 51
M(MUL_EXPR_TAIL, *) = 52
M(MUL_EXPR_TAIL, /) = 53
M(MUL_EXPR_TAIL, + ou - ou operador relacional ou ) ou ; ou ,) = 54
M(FACTOR, () = 55
M(FACTOR, id) = 56
M(FACTOR, num) = 57
M(FACTOR_TAIL, () = 58
M(FACTOR_TAIL, * ou / ou + ou - ou operador relacional ou ) ou ; ou ,) = 59
M(ARG_LIST_OPT, (/id/num) = 60
M(ARG_LIST_OPT, )) = 61
M(ARG_LIST, (/id/num) = 62
M(ARG_LIST_TAIL, ,) = 63
M(ARG_LIST_TAIL, )) = 64
M(TYPE, int) = 65
M(TYPE, float) = 66
```

## Mudancas em relacao a etapa anterior

O analisador sintatico principal deixou de ser uma descida recursiva por
metodos e passou a ser um analisador descendente preditivo tabular. A decisao
da producao vem da matriz `M(nao_terminal, token_atual)`, e a execucao mantem
uma pilha explicita iniciada com `$ PROGRAM`.

Essa mudanca atende a exigencia da E4: mostrar a pilha a cada modificacao,
usar uma tabela/matriz de analise sintatica e evitar backtracking.
