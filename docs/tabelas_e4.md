# E4 - Analisador Sintatico Preditivo Tabular

Este documento registra a gramatica usada pelo analisador sintatico tabular
implementado em `src/compilador.py`, suas tabelas FIRST/FOLLOW e a tabela
parser LL(1).

> Nota da versao final: para atender `AcoesSemantico.pdf`, o compilador atual
> aceita declaracoes globais `const nome = expressao;` antes da lista de
> funcoes. Na implementacao final, `PROGRAM` expande para
> `CONST_DECL_LIST_OPT FUNCTION_LIST`; a tabela abaixo preserva a base da E4
> original usada para a parte de funcoes, blocos, comandos e expressoes.

## Gramatica

```text
1  PROGRAM            -> FUNCTION_LIST
2  FUNCTION_LIST      -> FUNCTION FUNCTION_LIST_TAIL
3  FUNCTION_LIST_TAIL -> FUNCTION FUNCTION_LIST_TAIL
4  FUNCTION_LIST_TAIL -> epsilon
5  FUNCTION           -> TYPE id ( PARAM_LIST_OPT ) BLOCK
6  TYPE               -> int
7  TYPE               -> float
8  PARAM_LIST_OPT     -> PARAM_LIST
9  PARAM_LIST_OPT     -> epsilon
10 PARAM_LIST         -> PARAM PARAM_LIST_TAIL
11 PARAM_LIST_TAIL    -> , PARAM PARAM_LIST_TAIL
12 PARAM_LIST_TAIL    -> epsilon
13 PARAM              -> TYPE id
14 BLOCK              -> { DECL_LIST_OPT STMT_LIST_OPT }
15 DECL_LIST_OPT      -> DECL_LIST
16 DECL_LIST_OPT      -> epsilon
17 DECL_LIST          -> VAR_DECL DECL_LIST_TAIL
18 DECL_LIST_TAIL     -> VAR_DECL DECL_LIST_TAIL
19 DECL_LIST_TAIL     -> epsilon
20 VAR_DECL           -> TYPE id ;
21 STMT_LIST_OPT      -> STMT_LIST
22 STMT_LIST_OPT      -> epsilon
23 STMT_LIST          -> STMT STMT_LIST_TAIL
24 STMT_LIST_TAIL     -> STMT STMT_LIST_TAIL
25 STMT_LIST_TAIL     -> epsilon
26 STMT               -> ASSIGN_STMT
27 STMT               -> IF_STMT
28 STMT               -> WHILE_STMT
29 STMT               -> PRINT_STMT
30 STMT               -> RETURN_STMT
31 STMT               -> BLOCK
32 ASSIGN_STMT        -> id = EXPR ;
33 RETURN_STMT        -> return EXPR ;
34 PRINT_STMT         -> print ( EXPR ) ;
35 IF_STMT            -> if ( EXPR ) STMT ELSE_PART
36 ELSE_PART          -> else STMT
37 ELSE_PART          -> epsilon
38 WHILE_STMT         -> while ( EXPR ) STMT
39 EXPR               -> REL_EXPR
40 REL_EXPR           -> ADD_EXPR REL_EXPR_TAIL
41 REL_EXPR_TAIL      -> REL_OP ADD_EXPR
42 REL_EXPR_TAIL      -> epsilon
43 REL_OP             -> ==
44 REL_OP             -> !=
45 REL_OP             -> <
46 REL_OP             -> >
47 REL_OP             -> <=
48 REL_OP             -> >=
49 ADD_EXPR           -> MUL_EXPR ADD_EXPR_TAIL
50 ADD_EXPR_TAIL      -> + MUL_EXPR ADD_EXPR_TAIL
51 ADD_EXPR_TAIL      -> - MUL_EXPR ADD_EXPR_TAIL
52 ADD_EXPR_TAIL      -> epsilon
53 MUL_EXPR           -> FACTOR MUL_EXPR_TAIL
54 MUL_EXPR_TAIL      -> * FACTOR MUL_EXPR_TAIL
55 MUL_EXPR_TAIL      -> / FACTOR MUL_EXPR_TAIL
56 MUL_EXPR_TAIL      -> epsilon
57 FACTOR             -> ( EXPR )
58 FACTOR             -> id FACTOR_TAIL
59 FACTOR             -> num
60 FACTOR_TAIL        -> ( ARG_LIST_OPT )
61 FACTOR_TAIL        -> epsilon
62 ARG_LIST_OPT       -> ARG_LIST
63 ARG_LIST_OPT       -> epsilon
64 ARG_LIST           -> EXPR ARG_LIST_TAIL
65 ARG_LIST_TAIL      -> , EXPR ARG_LIST_TAIL
66 ARG_LIST_TAIL      -> epsilon
```

## FIRST

```text
PROGRAM:            int, float
FUNCTION_LIST:      int, float
FUNCTION_LIST_TAIL: int, float, epsilon
FUNCTION:           int, float
TYPE:               int, float
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
```

## FOLLOW

```text
PROGRAM:            $
FUNCTION_LIST:      $
FUNCTION_LIST_TAIL: $
FUNCTION:           int, float, $
TYPE:               id
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
```

## Tabela Parser LL(1)

As entradas da tabela indicam o numero da producao usada.

```text
M(PROGRAM, int/float) = 1
M(FUNCTION_LIST, int/float) = 2
M(FUNCTION_LIST_TAIL, int/float) = 3
M(FUNCTION_LIST_TAIL, $) = 4
M(FUNCTION, int/float) = 5
M(TYPE, int) = 6
M(TYPE, float) = 7
M(PARAM_LIST_OPT, int/float) = 8
M(PARAM_LIST_OPT, )) = 9
M(PARAM_LIST, int/float) = 10
M(PARAM_LIST_TAIL, ,) = 11
M(PARAM_LIST_TAIL, )) = 12
M(PARAM, int/float) = 13
M(BLOCK, {) = 14
M(DECL_LIST_OPT, int/float) = 15
M(DECL_LIST_OPT, id/if/while/print/return/{/}) = 16
M(DECL_LIST, int/float) = 17
M(DECL_LIST_TAIL, int/float) = 18
M(DECL_LIST_TAIL, id/if/while/print/return/{/}) = 19
M(VAR_DECL, int/float) = 20
M(STMT_LIST_OPT, id/if/while/print/return/{) = 21
M(STMT_LIST_OPT, }) = 22
M(STMT_LIST, id/if/while/print/return/{) = 23
M(STMT_LIST_TAIL, id/if/while/print/return/{) = 24
M(STMT_LIST_TAIL, }) = 25
M(STMT, id) = 26
M(STMT, if) = 27
M(STMT, while) = 28
M(STMT, print) = 29
M(STMT, return) = 30
M(STMT, {) = 31
M(ASSIGN_STMT, id) = 32
M(RETURN_STMT, return) = 33
M(PRINT_STMT, print) = 34
M(IF_STMT, if) = 35
M(ELSE_PART, else) = 36
M(ELSE_PART, id/if/while/print/return/{/}/$) = 37
M(WHILE_STMT, while) = 38
M(EXPR, (/id/num) = 39
M(REL_EXPR, (/id/num) = 40
M(REL_EXPR_TAIL, ==/!=/</>/<=/>=) = 41
M(REL_EXPR_TAIL, )/;/,) = 42
M(REL_OP, ==) = 43
M(REL_OP, !=) = 44
M(REL_OP, <) = 45
M(REL_OP, >) = 46
M(REL_OP, <=) = 47
M(REL_OP, >=) = 48
M(ADD_EXPR, (/id/num) = 49
M(ADD_EXPR_TAIL, +) = 50
M(ADD_EXPR_TAIL, -) = 51
M(ADD_EXPR_TAIL, ==/!=/</>/<=/>=/)/;/,) = 52
M(MUL_EXPR, (/id/num) = 53
M(MUL_EXPR_TAIL, *) = 54
M(MUL_EXPR_TAIL, /) = 55
M(MUL_EXPR_TAIL, + ou - ou operador relacional ou ) ou ; ou ,) = 56
M(FACTOR, () = 57
M(FACTOR, id) = 58
M(FACTOR, num) = 59
M(FACTOR_TAIL, () = 60
M(FACTOR_TAIL, * ou / ou + ou - ou operador relacional ou ) ou ; ou ,) = 61
M(ARG_LIST_OPT, (/id/num) = 62
M(ARG_LIST_OPT, )) = 63
M(ARG_LIST, (/id/num) = 64
M(ARG_LIST_TAIL, ,) = 65
M(ARG_LIST_TAIL, )) = 66
```

## Mudancas em relacao a etapa anterior

O analisador sintatico principal deixou de ser uma descida recursiva por
metodos e passou a ser um analisador descendente preditivo tabular. Agora a
decisao da producao vem da matriz `M(nao_terminal, token_atual)`, e a execucao
mantem uma pilha explicita iniciada com `$ PROGRAM`.

Essa mudanca foi feita para atender a exigencia da E4: mostrar a pilha a cada
modificacao, usar uma tabela/matriz de analise sintatica e evitar backtracking.
