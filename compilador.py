"""
Compilador / Analisador Léxico e Sintático
Linguagem: LangÇ# (baseada na gramática fornecida)
"""

import re
import sys
from enum import Enum, auto


# ─────────────────────────────────────────────
#  TOKENS
# ─────────────────────────────────────────────

class TokenType(Enum):
    # Tipos
    INT   = auto()
    FLOAT = auto()

    # Palavras-chave
    IF     = auto()
    ELSE   = auto()
    WHILE  = auto()
    PRINT  = auto()
    RETURN = auto()

    # Literais
    NUM   = auto()   # inteiro ou real
    ID    = auto()   # identificador

    # Operadores relacionais
    EQ  = auto()   # ==
    NEQ = auto()   # !=
    LT  = auto()   # <
    GT  = auto()   # >
    LEQ = auto()   # <=
    GEQ = auto()   # >=

    # Operadores aritméticos
    PLUS  = auto()   # +
    MINUS = auto()   # -
    STAR  = auto()   # *
    SLASH = auto()   # /

    # Atribuição
    ASSIGN = auto()  # =

    # Delimitadores
    LPAREN    = auto()   # (
    RPAREN    = auto()   # )
    LBRACE    = auto()   # {
    RBRACE    = auto()   # }
    SEMICOLON = auto()   # ;
    COMMA     = auto()   # ,

    # Fim
    EOF = auto()


KEYWORDS = {
    'int':    TokenType.INT,
    'float':  TokenType.FLOAT,
    'if':     TokenType.IF,
    'else':   TokenType.ELSE,
    'while':  TokenType.WHILE,
    'print':  TokenType.PRINT,
    'return': TokenType.RETURN,
}


class Token:
    def __init__(self, tipo: TokenType, valor, linha: int):
        self.tipo  = tipo
        self.valor = valor
        self.linha = linha

    def __repr__(self):
        return f"Token({self.tipo.name}, {self.valor!r}, linha={self.linha})"


# ─────────────────────────────────────────────
#  ERROS
# ─────────────────────────────────────────────

class ErroLexico(Exception):
    pass

class ErroSintatico(Exception):
    pass


# ─────────────────────────────────────────────
#  ANALISADOR LÉXICO
# ─────────────────────────────────────────────

class Lexer:
    """
    Transforma o código-fonte em uma sequência de tokens.

    Regras léxicas:
      • Identificadores: começam com letra ou '_', até 64 chars,
        sem acentos ou espaços.
      • Inteiros (num): sequência de dígitos.
      • Reais (num): dígitos '.' dígitos.
      • Comentários de linha: ç#
      • Comentários de bloco: ç@ ... @ç
    """

    def __init__(self, fonte: str):
        self.fonte  = fonte
        self.pos    = 0
        self.linha  = 1
        self.tokens: list[Token] = []

    # ── utilitários ──────────────────────────

    def _atual(self) -> str:
        return self.fonte[self.pos] if self.pos < len(self.fonte) else '\0'

    def _proximo(self) -> str:
        p = self.pos + 1
        return self.fonte[p] if p < len(self.fonte) else '\0'

    def _avanca(self) -> str:
        c = self._atual()
        self.pos += 1
        if c == '\n':
            self.linha += 1
        return c

    # ── tokenizar ────────────────────────────

    def tokenizar(self) -> list[Token]:
        while self.pos < len(self.fonte):
            self._pular_espacos_e_comentarios()
            if self.pos >= len(self.fonte):
                break

            c = self._atual()
            linha_atual = self.linha

            # ── estado ini: decisão por categoria de lexema ──
            if c.isalpha() or c == '_':
                # estado let: identificador/palavra-chave
                lexeme = ''
                while self._atual().isalnum() or self._atual() == '_':
                    lexeme += self._avanca()

                if len(lexeme) > 64:
                    raise ErroLexico(
                        f"Linha {linha_atual}: identificador '{lexeme[:20]}…' excede 64 caracteres"
                    )

                tipo = KEYWORDS.get(lexeme, TokenType.ID)
                self.tokens.append(Token(tipo, lexeme, linha_atual))

            elif c.isdigit():
                # estado dig: número inteiro ou real
                lexeme = ''
                while self._atual().isdigit():
                    lexeme += self._avanca()

                if self._atual() == '.' and self._proximo().isdigit():
                    # estado pont -> dig
                    lexeme += self._avanca()  # '.'
                    while self._atual().isdigit():
                        lexeme += self._avanca()

                self.tokens.append(Token(TokenType.NUM, lexeme, linha_atual))

            elif c == '=':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self.tokens.append(Token(TokenType.EQ, '==', linha_atual))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', linha_atual))

            elif c == '!':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self.tokens.append(Token(TokenType.NEQ, '!=', linha_atual))
                else:
                    raise ErroLexico(f"Linha {linha_atual}: operador '!' inválido, esperado '!='")

            elif c == '<':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self.tokens.append(Token(TokenType.LEQ, '<=', linha_atual))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', linha_atual))

            elif c == '>':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self.tokens.append(Token(TokenType.GEQ, '>=', linha_atual))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', linha_atual))

            elif c == '+':
                self._avanca(); self.tokens.append(Token(TokenType.PLUS, '+', linha_atual))
            elif c == '-':
                self._avanca(); self.tokens.append(Token(TokenType.MINUS, '-', linha_atual))
            elif c == '*':
                self._avanca(); self.tokens.append(Token(TokenType.STAR, '*', linha_atual))
            elif c == '/':
                # comentários resolvidos no estado de espaçamento/comentários
                self._avanca(); self.tokens.append(Token(TokenType.SLASH, '/', linha_atual))

            elif c == '(':
                self._avanca(); self.tokens.append(Token(TokenType.LPAREN, '(', linha_atual))
            elif c == ')':
                self._avanca(); self.tokens.append(Token(TokenType.RPAREN, ')', linha_atual))
            elif c == '{':
                self._avanca(); self.tokens.append(Token(TokenType.LBRACE, '{', linha_atual))
            elif c == '}':
                self._avanca(); self.tokens.append(Token(TokenType.RBRACE, '}', linha_atual))
            elif c == ';':
                self._avanca(); self.tokens.append(Token(TokenType.SEMICOLON, ';', linha_atual))
            elif c == ',':
                self._avanca(); self.tokens.append(Token(TokenType.COMMA, ',', linha_atual))

            else:
                raise ErroLexico(f"Linha {linha_atual}: caractere inesperado '{c}'")

        self.tokens.append(Token(TokenType.EOF, None, self.linha))
        return self.tokens

    # ── helpers ──────────────────────────────

    def _pular_espacos_e_comentarios(self):
        while self.pos < len(self.fonte):
            c = self._atual()
            if c in (' ', '\t', '\r', '\n'):
                self._avanca()
            elif c == 'ç':
                prox = self._proximo()
                if prox == '#':
                    # comentário de linha: ç#
                    self._avanca(); self._avanca()
                    while self.pos < len(self.fonte) and self._atual() != '\n':
                        self._avanca()
                elif prox == '@':
                    # comentário de bloco: ç@ ... @ç
                    self._avanca(); self._avanca()
                    fechado = False
                    while self.pos < len(self.fonte):
                        if self._atual() == '@' and self._proximo() == 'ç':
                            self._avanca(); self._avanca()
                            fechado = True
                            break
                        self._avanca()
                    if not fechado:
                        print(f"Aviso: comentário de bloco iniciado na linha {self.linha} não foi fechado com '@ç'")
                else:
                    # ç sem # ou @, aviso
                    print(f"Aviso: 'ç' encontrado na linha {self.linha}, esperado 'ç#' para comentário de linha ou 'ç@ ... @ç' para comentário de bloco")
                    break  # sai do loop, trata como token normal
            else:
                break

    def _ler_numero(self, linha: int) -> Token:
        inicio = self.pos
        while self._atual().isdigit():
            self._avanca()
        if self._atual() == '.' and self._proximo().isdigit():
            self._avanca()
            while self._atual().isdigit():
                self._avanca()
        valor = self.fonte[inicio:self.pos]
        return Token(TokenType.NUM, valor, linha)

    def _ler_id(self, linha: int) -> Token:
        inicio = self.pos
        while self._atual().isalnum() or self._atual() == '_':
            self._avanca()
        nome = self.fonte[inicio:self.pos]

        # Regra léxica: identificador até 64 chars
        if len(nome) > 64:
            raise ErroLexico(
                f"Linha {linha}: identificador '{nome[:20]}…' excede 64 caracteres"
            )

        tipo = KEYWORDS.get(nome, TokenType.ID)
        return Token(tipo, nome, linha)


# ─────────────────────────────────────────────
#  ANALISADOR SINTÁTICO  (LL recursivo)
# ─────────────────────────────────────────────
#
#  Implementa a gramática fornecida (regras 1-66).
#  Cada método corresponde a um não-terminal.

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos    = 0

    # ── utilitários ──────────────────────────

    @property
    def atual(self) -> Token:
        return self.tokens[self.pos]

    def _consome(self, tipo: TokenType) -> Token:
        tok = self.atual
        if tok.tipo != tipo:
            raise ErroSintatico(
                f"Linha {tok.linha}: esperado '{tipo.name}', "
                f"encontrado '{tok.tipo.name}' ({tok.valor!r})"
            )
        self.pos += 1
        return tok

    def _verifica(self, *tipos: TokenType) -> bool:
        return self.atual.tipo in tipos

    # ── FIRST sets (helpers) ─────────────────

    def _primeiro_tipo(self):
        return self._verifica(TokenType.INT, TokenType.FLOAT)

    def _primeiro_stmt(self):
        return self._verifica(
            TokenType.ID,
            TokenType.IF,
            TokenType.WHILE,
            TokenType.PRINT,
            TokenType.RETURN,
            TokenType.LBRACE,
        )

    # ── gramática ────────────────────────────

    # 1. <Program> ::= <FunctionList>
    def programa(self):
        self._function_list()
        self._consome(TokenType.EOF)
        print("✔  Análise sintática concluída sem erros.")

    # 2-4. <FunctionList>
    def _function_list(self):
        self._function()
        self._function_list_prime()

    def _function_list_prime(self):
        if self._primeiro_tipo():
            self._function()
            self._function_list_prime()
        # ε

    # 5. <Function> ::= <Type> id ( <ParamListOpt> ) <Block>
    def _function(self):
        self._type()
        self._consome(TokenType.ID)
        self._consome(TokenType.LPAREN)
        self._param_list_opt()
        self._consome(TokenType.RPAREN)
        self._block()

    # 6-7. <ParamListOpt>
    def _param_list_opt(self):
        if self._primeiro_tipo():
            self._param_list()
        # ε

    # 8-10. <ParamList>
    def _param_list(self):
        self._param()
        self._param_list_prime()

    def _param_list_prime(self):
        if self._verifica(TokenType.COMMA):
            self._consome(TokenType.COMMA)
            self._param()
            self._param_list_prime()
        # ε

    # 11. <Param> ::= <Type> id
    def _param(self):
        self._type()
        self._consome(TokenType.ID)

    # 12. <Block> ::= { <DeclListOpt> <StmtListOpt> }
    def _block(self):
        self._consome(TokenType.LBRACE)
        self._decl_list_opt()
        self._stmt_list_opt()
        self._consome(TokenType.RBRACE)

    # 13-17. <DeclListOpt> / <DeclList>
    def _decl_list_opt(self):
        # <DeclList> inicia com <Type>; mas <Stmt> também pode iniciar com <Type> via id
        # Usamos lookahead: Type seguido de id seguido de ';' → declaração
        if self._primeiro_tipo() and self._lookahead_decl():
            self._decl_list()
        # ε

    def _lookahead_decl(self) -> bool:
        """Verifica se os próximos tokens formam 'Type id ;'."""
        i = self.pos
        # tipo
        if i >= len(self.tokens): return False
        if self.tokens[i].tipo not in (TokenType.INT, TokenType.FLOAT): return False
        i += 1
        # id
        if i >= len(self.tokens): return False
        if self.tokens[i].tipo != TokenType.ID: return False
        i += 1
        # ';' → declaração de variável; '(' → função (não deve ocorrer aqui)
        if i >= len(self.tokens): return False
        return self.tokens[i].tipo == TokenType.SEMICOLON

    def _decl_list(self):
        self._var_decl()
        self._decl_list_prime()

    def _decl_list_prime(self):
        if self._primeiro_tipo() and self._lookahead_decl():
            self._var_decl()
            self._decl_list_prime()
        # ε

    # 18. <VarDecl> ::= <Type> id ;
    def _var_decl(self):
        self._type()
        self._consome(TokenType.ID)
        self._consome(TokenType.SEMICOLON)

    # 19-23. <StmtListOpt> / <StmtList>
    def _stmt_list_opt(self):
        if self._primeiro_stmt():
            self._stmt_list()
        # ε

    def _stmt_list(self):
        self._stmt()
        self._stmt_list_prime()

    def _stmt_list_prime(self):
        if self._primeiro_stmt():
            self._stmt()
            self._stmt_list_prime()
        # ε

    # 24-29. <Stmt>
    def _stmt(self):
        t = self.atual.tipo
        if t == TokenType.ID:          self._assign_stmt()
        elif t == TokenType.IF:        self._if_stmt()
        elif t == TokenType.WHILE:     self._while_stmt()
        elif t == TokenType.PRINT:     self._print_stmt()
        elif t == TokenType.RETURN:    self._return_stmt()
        elif t == TokenType.LBRACE:    self._block()
        else:
            raise ErroSintatico(
                f"Linha {self.atual.linha}: statement inválido (token '{t.name}')"
            )

    # 30. <AssignStmt> ::= id = <Expr> ;
    def _assign_stmt(self):
        self._consome(TokenType.ID)
        self._consome(TokenType.ASSIGN)
        self._expr()
        self._consome(TokenType.SEMICOLON)

    # 31. <ReturnStmt> ::= return <Expr> ;
    def _return_stmt(self):
        self._consome(TokenType.RETURN)
        self._expr()
        self._consome(TokenType.SEMICOLON)

    # 32. <PrintStmt> ::= print ( <Expr> ) ;
    def _print_stmt(self):
        self._consome(TokenType.PRINT)
        self._consome(TokenType.LPAREN)
        self._expr()
        self._consome(TokenType.RPAREN)
        self._consome(TokenType.SEMICOLON)

    # 33. <IfStmt> ::= if ( <Expr> ) <Stmt> <ElsePart>
    def _if_stmt(self):
        self._consome(TokenType.IF)
        self._consome(TokenType.LPAREN)
        self._expr()
        self._consome(TokenType.RPAREN)
        self._stmt()
        self._else_part()

    # 34-35. <ElsePart>
    def _else_part(self):
        if self._verifica(TokenType.ELSE):
            self._consome(TokenType.ELSE)
            self._stmt()
        # ε

    # 36. <WhileStmt> ::= while ( <Expr> ) <Stmt>
    def _while_stmt(self):
        self._consome(TokenType.WHILE)
        self._consome(TokenType.LPAREN)
        self._expr()
        self._consome(TokenType.RPAREN)
        self._stmt()

    # 37. <Expr> ::= <RelExpr>
    def _expr(self):
        self._rel_expr()

    # 38-40. <RelExpr>
    REL_OPS = {TokenType.EQ, TokenType.NEQ, TokenType.LT,
               TokenType.GT, TokenType.LEQ, TokenType.GEQ}

    def _rel_expr(self):
        self._add_expr()
        self._rel_expr_prime()

    def _rel_expr_prime(self):
        if self.atual.tipo in self.REL_OPS:
            self._rel_op()
            self._add_expr()
        # ε

    # 41-46. <RelOp>
    def _rel_op(self):
        if self.atual.tipo in self.REL_OPS:
            self.pos += 1
        else:
            raise ErroSintatico(
                f"Linha {self.atual.linha}: operador relacional esperado"
            )

    # 47-50. <AddExpr>
    def _add_expr(self):
        self._mul_expr()
        self._add_expr_prime()

    def _add_expr_prime(self):
        if self._verifica(TokenType.PLUS):
            self._consome(TokenType.PLUS)
            self._mul_expr()
            self._add_expr_prime()
        elif self._verifica(TokenType.MINUS):
            self._consome(TokenType.MINUS)
            self._mul_expr()
            self._add_expr_prime()
        # ε

    # 51-54. <MulExpr>
    def _mul_expr(self):
        self._factor()
        self._mul_expr_prime()

    def _mul_expr_prime(self):
        if self._verifica(TokenType.STAR):
            self._consome(TokenType.STAR)
            self._factor()
            self._mul_expr_prime()
        elif self._verifica(TokenType.SLASH):
            self._consome(TokenType.SLASH)
            self._factor()
            self._mul_expr_prime()
        # ε

    # 55-57. <Factor>
    def _factor(self):
        if self._verifica(TokenType.LPAREN):
            self._consome(TokenType.LPAREN)
            self._expr()
            self._consome(TokenType.RPAREN)
        elif self._verifica(TokenType.ID):
            self._consome(TokenType.ID)
            self._factor_tail()
        elif self._verifica(TokenType.NUM):
            self._consome(TokenType.NUM)
        else:
            raise ErroSintatico(
                f"Linha {self.atual.linha}: fator inválido (token '{self.atual.tipo.name}')"
            )

    # 58-59. <FactorTail>
    def _factor_tail(self):
        if self._verifica(TokenType.LPAREN):
            self._consome(TokenType.LPAREN)
            self._arg_list_opt()
            self._consome(TokenType.RPAREN)
        # ε

    # 60-64. <ArgListOpt> / <ArgList>
    def _arg_list_opt(self):
        if not self._verifica(TokenType.RPAREN):
            self._arg_list()
        # ε

    def _arg_list(self):
        self._expr()
        self._arg_list_prime()

    def _arg_list_prime(self):
        if self._verifica(TokenType.COMMA):
            self._consome(TokenType.COMMA)
            self._expr()
            self._arg_list_prime()
        # ε

    # 65-66. <Type>
    def _type(self):
        if self._verifica(TokenType.INT):
            self._consome(TokenType.INT)
        elif self._verifica(TokenType.FLOAT):
            self._consome(TokenType.FLOAT)
        else:
            raise ErroSintatico(
                f"Linha {self.atual.linha}: tipo esperado (int ou float), "
                f"encontrado '{self.atual.tipo.name}'"
            )


# ─────────────────────────────────────────────
#  INTERFACE PRINCIPAL
# ─────────────────────────────────────────────

EXEMPLO_CODIGO = """\
ç# Calcula o fatorial de n de forma recursiva
int fatorial(int n) {
    int resultado;
    if (n <= 1) {
        resultado = 1;
        return resultado;
    }
    resultado = n * fatorial(n - 1);
    return resultado;
}

ç# Verifica se um número é par
int ehPar(int x) {
    int resto;
    resto = x - (x / 2) * 2;
    return resto;
}

ç
    Programa principal que imprime os fatoriais de 1 a 5.
    Usa comentários de bloco para documentação.
    int main() é a função de entrada.
@ç

ç# Função principal
int main() {
    int i;
    int val;
    i = 1;
    while (i <= 5) {
        val = fatorial(i);
        print(val);
        i = i + 1;
    }
    return 0;
}
"""


def compilar(fonte: str, mostrar_tokens: bool = False):
    print("═" * 50)
    print("  COMPILADOR LangÇ#")
    print("═" * 50)

    # Fase 1 — Léxico
    print("\n[1] Análise Léxica...")
    try:
        lexer  = Lexer(fonte)
        tokens = lexer.tokenizar()
        print(f"    {len(tokens) - 1} token(s) gerado(s).")
        if mostrar_tokens:
            for tok in tokens[:-1]:
                print(f"    {tok}")
    except ErroLexico as e:
        print(f"    ERRO LÉXICO: {e}")
        return

    # Fase 2 — Sintático
    print("\n[2] Análise Sintática...")
    try:
        parser = Parser(tokens)
        parser.programa()
    except ErroSintatico as e:
        print(f"    ERRO SINTÁTICO: {e}")
        return

    print("\n  Compilação finalizada com sucesso!")
    print("═" * 50)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            codigo = f.read()
        compilar(codigo, mostrar_tokens='--tokens' in sys.argv)
    else:
        # Roda o exemplo embutido
        print("Uso: python compilador.py <arquivo.lcc> [--tokens]")
        print("Executando exemplo interno...\n")
        compilar(EXEMPLO_CODIGO, mostrar_tokens=True)
