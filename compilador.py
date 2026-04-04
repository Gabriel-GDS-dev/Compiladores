"""
Compilador / Analisador Léxico e Sintático
Linguagem: LangÇ# (baseada na gramática fornecida)

Estrutura de transformação em um único arquivo:
1. O programa localiza arquivos .txt na pasta do script.
2. O usuário escolhe um arquivo por número.
3. O Lexer lê o conteúdo e gera como estrutura principal três vetores paralelos:
   - tokens  -> códigos numéricos exatos dos tokens
   - lexemas -> lexemas reconhecidos
   - linhas  -> linha original de cada token
4. Esses vetores são usados diretamente para:
   - exibição no terminal
   - exportação JSON
5. Para preservar o Parser sem reescrever sua lógica, os vetores são
   convertidos localmente em objetos Token apenas antes da análise sintática.
"""

import json
from pathlib import Path
from enum import Enum


# ─────────────────────────────────────────────
#  TOKENS
# ─────────────────────────────────────────────

class TokenType(Enum):
    INT        = 1   # int
    FLOAT      = 2   # float
    IF         = 3   # if
    ELSE       = 4   # else
    WHILE      = 5   # while
    RETURN     = 6   # return
    PRINT      = 7   # print
    ID         = 8   # id
    NUM        = 9   # num
    ASSIGN     = 10  # =
    PLUS       = 11  # +
    MINUS      = 12  # -
    STAR       = 13  # *
    SLASH      = 14  # /
    EQ         = 15  # ==
    NEQ        = 16  # !=
    LT         = 17  # <
    GT         = 18  # >
    LEQ        = 19  # <=
    GEQ        = 20  # >=
    LPAREN     = 21  # (
    RPAREN     = 22  # )
    LBRACE     = 23  # {
    RBRACE     = 24  # }
    COMMA      = 25  # ,
    SEMICOLON  = 26  # ;
    EOF        = 27  # $


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
        self.tipo = tipo
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
    Estrutura principal da saída léxica:
      self.tokens_codigos -> vetor com os códigos numéricos exatos
      self.lexemas        -> vetor com os lexemas
      self.linhas         -> vetor com as linhas correspondentes

    Regras léxicas:
      • Identificadores: começam com letra ou '_', até 64 chars.
      • Inteiros (num): sequência de dígitos.
      • Reais (num): dígitos '.' dígitos.
      • Comentários de linha: ç#
      • Comentários de bloco: ç@ ... @ç
    """

    def __init__(self, fonte: str):
        self.fonte = fonte
        self.pos = 0
        self.linha = 1

        # Estrutura principal baseada em vetores
        self.tokens_codigos: list[int] = []
        self.lexemas: list[str | None] = []
        self.linhas: list[int] = []

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

    def _adiciona_token(self, tipo: TokenType, valor, linha: int):
        self.tokens_codigos.append(tipo.value)
        self.lexemas.append(valor)
        self.linhas.append(linha)

    # ── tokenizar ────────────────────────────

    def tokenizar(self) -> tuple[list[int], list[str | None], list[int]]:
        while self.pos < len(self.fonte):
            self._pular_espacos_e_comentarios()
            if self.pos >= len(self.fonte):
                break

            c = self._atual()
            linha_atual = self.linha

            if c.isalpha() or c == '_':
                lexeme = ''
                while self._atual().isalnum() or self._atual() == '_':
                    lexeme += self._avanca()

                if len(lexeme) > 64:
                    raise ErroLexico(
                        f"Linha {linha_atual}: identificador '{lexeme[:20]}…' excede 64 caracteres"
                    )

                tipo = KEYWORDS.get(lexeme, TokenType.ID)
                self._adiciona_token(tipo, lexeme, linha_atual)

            elif c.isdigit():
                lexeme = ''
                while self._atual().isdigit():
                    lexeme += self._avanca()

                if self._atual() == '.' and self._proximo().isdigit():
                    lexeme += self._avanca()
                    while self._atual().isdigit():
                        lexeme += self._avanca()

                self._adiciona_token(TokenType.NUM, lexeme, linha_atual)

            elif c == '=':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.EQ, '==', linha_atual)
                else:
                    self._adiciona_token(TokenType.ASSIGN, '=', linha_atual)

            elif c == '!':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.NEQ, '!=', linha_atual)
                else:
                    raise ErroLexico(f"Linha {linha_atual}: operador '!' inválido, esperado '!='")

            elif c == '<':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.LEQ, '<=', linha_atual)
                else:
                    self._adiciona_token(TokenType.LT, '<', linha_atual)

            elif c == '>':
                self._avanca()
                if self._atual() == '=':
                    self._avanca()
                    self._adiciona_token(TokenType.GEQ, '>=', linha_atual)
                else:
                    self._adiciona_token(TokenType.GT, '>', linha_atual)

            elif c == '+':
                self._avanca()
                self._adiciona_token(TokenType.PLUS, '+', linha_atual)

            elif c == '-':
                self._avanca()
                self._adiciona_token(TokenType.MINUS, '-', linha_atual)

            elif c == '*':
                self._avanca()
                self._adiciona_token(TokenType.STAR, '*', linha_atual)

            elif c == '/':
                self._avanca()
                self._adiciona_token(TokenType.SLASH, '/', linha_atual)

            elif c == '(':
                self._avanca()
                self._adiciona_token(TokenType.LPAREN, '(', linha_atual)

            elif c == ')':
                self._avanca()
                self._adiciona_token(TokenType.RPAREN, ')', linha_atual)

            elif c == '{':
                self._avanca()
                self._adiciona_token(TokenType.LBRACE, '{', linha_atual)

            elif c == '}':
                self._avanca()
                self._adiciona_token(TokenType.RBRACE, '}', linha_atual)

            elif c == ';':
                self._avanca()
                self._adiciona_token(TokenType.SEMICOLON, ';', linha_atual)

            elif c == ',':
                self._avanca()
                self._adiciona_token(TokenType.COMMA, ',', linha_atual)

            else:
                raise ErroLexico(f"Linha {linha_atual}: caractere inesperado '{c}'")

        self._adiciona_token(TokenType.EOF, '$', self.linha)
        return self.tokens_codigos, self.lexemas, self.linhas

    # ── helpers ──────────────────────────────

    def _pular_espacos_e_comentarios(self):
        while self.pos < len(self.fonte):
            c = self._atual()
            if c in (' ', '\t', '\r', '\n'):
                self._avanca()
            elif c == 'ç':
                prox = self._proximo()
                if prox == '#':
                    self._avanca()
                    self._avanca()
                    while self.pos < len(self.fonte) and self._atual() != '\n':
                        self._avanca()
                elif prox == '@':
                    linha_inicio = self.linha
                    self._avanca()
                    self._avanca()
                    fechado = False
                    while self.pos < len(self.fonte):
                        if self._atual() == '@' and self._proximo() == 'ç':
                            self._avanca()
                            self._avanca()
                            fechado = True
                            break
                        self._avanca()
                    if not fechado:
                        print(f"Aviso: comentário de bloco iniciado na linha {linha_inicio} não foi fechado com '@ç'")
                else:
                    print(f"Aviso: 'ç' encontrado na linha {self.linha}, esperado 'ç#' para comentário de linha ou 'ç@ ... @ç' para comentário de bloco")
                    break
            else:
                break


def vetores_para_tokens(tokens_codigos: list[int], lexemas: list[str | None], linhas: list[int]) -> list[Token]:
    return [
        Token(TokenType(codigo), lexema, linha)
        for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas)
    ]


# ─────────────────────────────────────────────
#  ANALISADOR SINTÁTICO  (LL recursivo)
# ─────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    @property
    def atual(self) -> Token:
        return self.tokens[self.pos]

    def _simbolo_token(self, tipo: TokenType) -> str:
        simbolos = {
            TokenType.INT: 'int',
            TokenType.FLOAT: 'float',
            TokenType.IF: 'if',
            TokenType.ELSE: 'else',
            TokenType.WHILE: 'while',
            TokenType.RETURN: 'return',
            TokenType.PRINT: 'print',
            TokenType.ID: 'identificador',
            TokenType.NUM: 'número',
            TokenType.ASSIGN: '=',
            TokenType.PLUS: '+',
            TokenType.MINUS: '-',
            TokenType.STAR: '*',
            TokenType.SLASH: '/',
            TokenType.EQ: '==',
            TokenType.NEQ: '!=',
            TokenType.LT: '<',
            TokenType.GT: '>',
            TokenType.LEQ: '<=',
            TokenType.GEQ: '>=',
            TokenType.LPAREN: '(',
            TokenType.RPAREN: ')',
            TokenType.LBRACE: '{',
            TokenType.RBRACE: '}',
            TokenType.COMMA: ',',
            TokenType.SEMICOLON: ';',
            TokenType.EOF: '$',
        }
        return simbolos.get(tipo, tipo.name)

    def _formatar_token_encontrado(self, tok: Token) -> str:
        if tok.tipo == TokenType.EOF:
            return "fim de entrada '$'"
        if tok.valor is None:
            return f"token {tok.tipo.name}"
        return f"{tok.valor!r}"

    def _mensagem_erro_esperado(self, esperado: TokenType, encontrado: Token) -> str:
        anterior = self.tokens[self.pos - 1] if self.pos > 0 else encontrado

        if esperado == TokenType.SEMICOLON:
            return (
                f"Linha {anterior.linha}: faltou ';' ao final da instrução "
                f"antes de {self._formatar_token_encontrado(encontrado)} "
                f"(linha {encontrado.linha})"
            )

        if esperado == TokenType.RPAREN:
            return (
                f"Linha {anterior.linha}: faltou ')' antes de "
                f"{self._formatar_token_encontrado(encontrado)} "
                f"(linha {encontrado.linha})"
            )

        if esperado == TokenType.RBRACE:
            simbolo = "}"
            return (
                f"Linha {anterior.linha}: faltou '{simbolo}' antes de "
                f"{self._formatar_token_encontrado(encontrado)} "
                f"(linha {encontrado.linha})"
            )

        if esperado == TokenType.LPAREN:
            return (
                f"Linha {anterior.linha}: faltou '(' após "
                f"{self._formatar_token_encontrado(anterior)}"
            )

        if esperado == TokenType.ID and anterior.tipo in (TokenType.INT, TokenType.FLOAT):
            return (
                f"Linha {encontrado.linha}: esperado identificador após o tipo "
                f"{self._formatar_token_encontrado(anterior)}, "
                f"mas encontrado {self._formatar_token_encontrado(encontrado)}"
            )

        return (
            f"Linha {encontrado.linha}: esperado '{self._simbolo_token(esperado)}', "
            f"encontrado {self._formatar_token_encontrado(encontrado)}"
        )

    def _consome(self, tipo: TokenType) -> Token:
        tok = self.atual
        if tok.tipo != tipo:
            raise ErroSintatico(self._mensagem_erro_esperado(tipo, tok))
        self.pos += 1
        return tok

    def _verifica(self, *tipos: TokenType) -> bool:
        return self.atual.tipo in tipos

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

    def programa(self):
        self._function_list()
        self._consome(TokenType.EOF)
        print("✔  Análise sintática concluída sem erros.")

    def _function_list(self):
        self._function()
        self._function_list_prime()

    def _function_list_prime(self):
        if self._primeiro_tipo():
            self._function()
            self._function_list_prime()

    def _function(self):
        self._type()
        self._consome(TokenType.ID)

        # No nível global, a gramática aceita apenas funções.
        # Isso evita uma mensagem pouco útil quando aparece algo como:
        #   int x;
        if self._verifica(TokenType.SEMICOLON):
            raise ErroSintatico(
                f"Linha {self.atual.linha}: declaração global de variável não é permitida; esperado 'LPAREN'"
            )

        self._consome(TokenType.LPAREN)
        self._param_list_opt()
        self._consome(TokenType.RPAREN)
        self._block()

    def _param_list_opt(self):
        if self._primeiro_tipo():
            self._param_list()

    def _param_list(self):
        self._param()
        self._param_list_prime()

    def _param_list_prime(self):
        if self._verifica(TokenType.COMMA):
            self._consome(TokenType.COMMA)
            self._param()
            self._param_list_prime()

    def _param(self):
        self._type()
        self._consome(TokenType.ID)

    def _block(self):
        self._consome(TokenType.LBRACE)
        self._decl_list_opt()
        self._stmt_list_opt()

        # Se ainda houver um tipo aqui, então apareceu uma declaração depois
        # do início dos statements do bloco, o que é inválido nesta gramática.
        # Sem essa checagem, o parser acabava acusando apenas 'esperado RBRACE'.
        if self._primeiro_tipo():
            raise ErroSintatico(
                f"Linha {self.atual.linha}: declaração não permitida após statements no bloco"
            )

        self._consome(TokenType.RBRACE)

    def _decl_list_opt(self):
        # Dentro de bloco, qualquer token de tipo (int/float) inicia declaração.
        # Não exigimos ';' no lookahead, porque isso mascara erros como:
        #   int x
        # e faz o parser reportar incorretamente 'esperado RBRACE'.
        if self._primeiro_tipo():
            self._decl_list()

    def _lookahead_decl(self) -> bool:
        # Método mantido apenas por compatibilidade/minimizar mudanças.
        # A decisão de declaração no bloco agora é feita por _primeiro_tipo().
        i = self.pos
        if i >= len(self.tokens):
            return False
        if self.tokens[i].tipo not in (TokenType.INT, TokenType.FLOAT):
            return False
        i += 1
        if i >= len(self.tokens):
            return False
        return self.tokens[i].tipo == TokenType.ID

    def _decl_list(self):
        self._var_decl()
        self._decl_list_prime()

    def _decl_list_prime(self):
        if self._primeiro_tipo():
            self._var_decl()
            self._decl_list_prime()

    def _var_decl(self):
        self._type()
        self._consome(TokenType.ID)
        self._consome(TokenType.SEMICOLON)

    def _stmt_list_opt(self):
        if self._primeiro_stmt():
            self._stmt_list()

    def _stmt_list(self):
        self._stmt()
        self._stmt_list_prime()

    def _stmt_list_prime(self):
        if self._primeiro_stmt():
            self._stmt()
            self._stmt_list_prime()

    def _stmt(self):
        t = self.atual.tipo
        if t == TokenType.ID:
            self._assign_stmt()
        elif t == TokenType.IF:
            self._if_stmt()
        elif t == TokenType.WHILE:
            self._while_stmt()
        elif t == TokenType.PRINT:
            self._print_stmt()
        elif t == TokenType.RETURN:
            self._return_stmt()
        elif t == TokenType.LBRACE:
            self._block()
        else:
            raise ErroSintatico(
                f"Linha {self.atual.linha}: statement inválido (token '{t.name}')"
            )

    def _assign_stmt(self):
        self._consome(TokenType.ID)
        self._consome(TokenType.ASSIGN)
        self._expr()
        self._consome(TokenType.SEMICOLON)

    def _return_stmt(self):
        self._consome(TokenType.RETURN)
        self._expr()
        self._consome(TokenType.SEMICOLON)

    def _print_stmt(self):
        self._consome(TokenType.PRINT)
        self._consome(TokenType.LPAREN)
        self._expr()
        self._consome(TokenType.RPAREN)
        self._consome(TokenType.SEMICOLON)

    def _if_stmt(self):
        self._consome(TokenType.IF)
        self._consome(TokenType.LPAREN)
        self._expr()
        self._consome(TokenType.RPAREN)
        self._stmt()
        self._else_part()

    def _else_part(self):
        if self._verifica(TokenType.ELSE):
            self._consome(TokenType.ELSE)
            self._stmt()

    def _while_stmt(self):
        self._consome(TokenType.WHILE)
        self._consome(TokenType.LPAREN)
        self._expr()
        self._consome(TokenType.RPAREN)
        self._stmt()

    def _expr(self):
        self._rel_expr()

    REL_OPS = {
        TokenType.EQ, TokenType.NEQ, TokenType.LT,
        TokenType.GT, TokenType.LEQ, TokenType.GEQ
    }

    def _rel_expr(self):
        self._add_expr()
        self._rel_expr_prime()

    def _rel_expr_prime(self):
        if self.atual.tipo in self.REL_OPS:
            self._rel_op()
            self._add_expr()

    def _rel_op(self):
        if self.atual.tipo in self.REL_OPS:
            self.pos += 1
        else:
            raise ErroSintatico(
                f"Linha {self.atual.linha}: operador relacional esperado"
            )

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

    def _factor_tail(self):
        if self._verifica(TokenType.LPAREN):
            self._consome(TokenType.LPAREN)
            self._arg_list_opt()
            self._consome(TokenType.RPAREN)

    def _arg_list_opt(self):
        if not self._verifica(TokenType.RPAREN):
            self._arg_list()

    def _arg_list(self):
        self._expr()
        self._arg_list_prime()

    def _arg_list_prime(self):
        if self._verifica(TokenType.COMMA):
            self._consome(TokenType.COMMA)
            self._expr()
            self._arg_list_prime()

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
#  FUNÇÕES AUXILIARES DE ENTRADA/SAÍDA
# ─────────────────────────────────────────────

def obter_pasta_script() -> Path:
    return Path(__file__).resolve().parent


def listar_arquivos_txt(pasta: Path) -> list[Path]:
    return sorted(
        [arquivo for arquivo in pasta.iterdir() if arquivo.is_file() and arquivo.suffix.lower() == '.txt'],
        key=lambda arquivo: arquivo.name.lower(),
    )


def escolher_arquivo(arquivos: list[Path]) -> Path:
    print("Arquivos .txt encontrados:")
    for i, arquivo in enumerate(arquivos, start=1):
        print(f"  {i} - {arquivo.name}")

    while True:
        escolha = input("\nDigite o número do arquivo que deseja analisar: ").strip()

        if not escolha:
            print("Entrada vazia. Digite um número da lista.")
            continue

        if not escolha.isdigit():
            print("Entrada inválida. Digite apenas o número do arquivo.")
            continue

        indice = int(escolha)
        if 1 <= indice <= len(arquivos):
            return arquivos[indice - 1]

        print(f"Número fora do intervalo. Escolha entre 1 e {len(arquivos)}.")


def ler_arquivo(caminho: Path) -> str:
    try:
        with caminho.open('r', encoding='utf-8') as arquivo:
            return arquivo.read()
    except OSError as e:
        raise RuntimeError(f"Erro ao abrir o arquivo '{caminho.name}': {e}") from e
    except UnicodeDecodeError as e:
        raise RuntimeError(
            f"Erro ao ler '{caminho.name}': o arquivo não está em UTF-8 válido."
        ) from e


def mostrar_tabela_tokens(tokens_codigos: list[int], lexemas: list[str | None], linhas: list[int], incluir_eof: bool = False):
    registros = []
    for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas):
        if not incluir_eof and codigo == TokenType.EOF.value:
            continue
        registros.append((codigo, lexema, linha))

    if not registros:
        print("Nenhum token para exibir.")
        return

    nomes = [TokenType(codigo).name for codigo, _, _ in registros]
    lexemas_formatados = ["" if lexema is None else str(lexema) for _, lexema, _ in registros]

    largura_token = max(len("TOKEN"), max(len(nome) for nome in nomes))
    largura_lexema = max(len("LEXEMA"), max(len(lex) for lex in lexemas_formatados))

    cabecalho = f"{'TOKEN':<{largura_token}} | {'LEXEMA':<{largura_lexema}} | LINHA"
    print("\n" + cabecalho)
    print("-" * len(cabecalho))

    for (codigo, lexema, linha), nome in zip(registros, nomes):
        lexema_texto = "" if lexema is None else str(lexema)
        print(f"{nome:<{largura_token}} | {lexema_texto:<{largura_lexema}} | {linha}")


def exportar_tokens_json(tokens_codigos: list[int], lexemas: list[str | None], linhas: list[int], caminho_txt: Path) -> Path:
    tokens_sem_eof = []
    lexemas_sem_eof = []
    linhas_sem_eof = []

    for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas):
        if codigo == TokenType.EOF.value:
            continue
        tokens_sem_eof.append(codigo)
        lexemas_sem_eof.append("" if lexema is None else str(lexema))
        linhas_sem_eof.append(linha)

    dados = {
        "tokens": tokens_sem_eof,
        "lexemas": lexemas_sem_eof,
        "linhas": linhas_sem_eof,
    }

    caminho_json = caminho_txt.with_name(f"{caminho_txt.stem}_tokens.json")
    with caminho_json.open('w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)

    return caminho_json


# ─────────────────────────────────────────────
#  INTERFACE PRINCIPAL
# ─────────────────────────────────────────────

def compilar(fonte: str, mostrar_tokens: bool = True):
    print("═" * 50)
    print("  COMPILADOR LangÇ#")
    print("═" * 50)

    print("\n[1] Análise Léxica...")
    try:
        lexer = Lexer(fonte)
        tokens_codigos, lexemas, linhas = lexer.tokenizar()
        quantidade_sem_eof = sum(1 for codigo in tokens_codigos if codigo != TokenType.EOF.value)
        print(f"    {quantidade_sem_eof} token(s) gerado(s).")
        if mostrar_tokens:
            mostrar_tabela_tokens(tokens_codigos, lexemas, linhas)
    except ErroLexico as e:
        print(f"    ERRO LÉXICO: {e}")
        return None, None, None, False

    print("\n[2] Análise Sintática...")
    try:
        tokens_parser = vetores_para_tokens(tokens_codigos, lexemas, linhas)
        parser = Parser(tokens_parser)
        parser.programa()
    except ErroSintatico as e:
        print(f"    ERRO SINTÁTICO: {e}")
        return tokens_codigos, lexemas, linhas, False

    print("\n  Compilação finalizada com sucesso!")
    print("═" * 50)
    return tokens_codigos, lexemas, linhas, True


if __name__ == "__main__":
    pasta_script = obter_pasta_script()
    arquivos_txt = listar_arquivos_txt(pasta_script)

    if not arquivos_txt:
        print(f"Nenhum arquivo .txt encontrado na pasta do script: {pasta_script}")
    else:
        arquivo_escolhido = escolher_arquivo(arquivos_txt)
        print(f"\nArquivo selecionado: {arquivo_escolhido.name}")

        try:
            codigo = ler_arquivo(arquivo_escolhido)
        except RuntimeError as e:
            print(e)
        else:
            tokens_codigos, lexemas, linhas, _ = compilar(codigo, mostrar_tokens=True)
            if tokens_codigos is not None:
                try:
                    caminho_json = exportar_tokens_json(tokens_codigos, lexemas, linhas, arquivo_escolhido)
                    print(f"\n[3] Tokens exportados em JSON: {caminho_json.name}")
                except OSError as e:
                    print(f"\n[3] Não foi possível exportar o JSON: {e}")
