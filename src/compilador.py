# -*- coding: utf-8 -*-
"""
Compilador LangC# em arquivo unico.

Inclui:
- analisador lexico conforme o manual da linguagem;
- analisador sintatico preditivo tabular LL(1);
- analisador semantico com tabela de simbolos, constantes, escopos e tipos;
- exportacao JSON de tokens;
- relatorio HTML completo, sem prompt interativo.
"""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_EXEMPLOS = RAIZ_PROJETO / "examples"
PASTA_LANGC = PASTA_EXEMPLOS / "langc"
PASTA_SEMANTICO = PASTA_EXEMPLOS / "semantico"
PASTA_TOKENS = RAIZ_PROJETO / "outputs" / "tokens"
PASTA_RELATORIOS = RAIZ_PROJETO / "outputs" / "reports"


class TokenType(Enum):
    INT = 1
    FLOAT = 2
    IF = 3
    ELSE = 4
    WHILE = 5
    RETURN = 6
    PRINT = 7
    ID = 8
    NUM = 9
    ASSIGN = 10
    PLUS = 11
    MINUS = 12
    STAR = 13
    SLASH = 14
    EQ = 15
    NEQ = 16
    LT = 17
    GT = 18
    LEQ = 19
    GEQ = 20
    LPAREN = 21
    RPAREN = 22
    LBRACE = 23
    RBRACE = 24
    COMMA = 25
    SEMICOLON = 26
    EOF = 27
    CONST = 28


KEYWORDS = {
    "int": TokenType.INT,
    "float": TokenType.FLOAT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "print": TokenType.PRINT,
    "const": TokenType.CONST,
}


TOKEN_TEXT = {
    TokenType.INT: "int",
    TokenType.FLOAT: "float",
    TokenType.IF: "if",
    TokenType.ELSE: "else",
    TokenType.WHILE: "while",
    TokenType.RETURN: "return",
    TokenType.PRINT: "print",
    TokenType.CONST: "const",
    TokenType.ID: "id",
    TokenType.NUM: "num",
    TokenType.ASSIGN: "=",
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.EQ: "==",
    TokenType.NEQ: "!=",
    TokenType.LT: "<",
    TokenType.GT: ">",
    TokenType.LEQ: "<=",
    TokenType.GEQ: ">=",
    TokenType.LPAREN: "(",
    TokenType.RPAREN: ")",
    TokenType.LBRACE: "{",
    TokenType.RBRACE: "}",
    TokenType.COMMA: ",",
    TokenType.SEMICOLON: ";",
    TokenType.EOF: "$",
}


class ErroLexico(Exception):
    pass


class ErroSintatico(Exception):
    pass


class ErroSemantico(Exception):
    pass


@dataclass(slots=True)
class Token:
    tipo: TokenType
    valor: str
    linha: int
    coluna: int

    @property
    def lexema(self) -> str:
        return self.valor

    def __repr__(self) -> str:
        return f"Token({self.tipo.name}, {self.valor!r}, linha={self.linha}, coluna={self.coluna})"


@dataclass
class PassoSintatico:
    passo: int
    codigo_token: int
    token: str
    lexema: str
    linha: int
    pilha: str
    acao: str


@dataclass
class Simbolo:
    nome: str
    categoria: str
    tipo: str
    nivel: int
    linha: int
    escopo: str
    parametros: list[str] = field(default_factory=list)


@dataclass
class EventoSemantico:
    passo: int
    etapa: str
    detalhe: str
    linha: int | None = None
    status: str = "OK"


@dataclass
class ResultadoCompilacao:
    origem: str
    codigo: str
    tokens: list[Token] = field(default_factory=list)
    passos_sintaticos: list[PassoSintatico] = field(default_factory=list)
    simbolos: list[Simbolo] = field(default_factory=list)
    eventos_semanticos: list[EventoSemantico] = field(default_factory=list)
    sucesso: bool = False
    fase: str = "inicio"
    diagnostico: str = ""
    relatorio: Path | None = None
    json_tokens: Path | None = None


def eh_letra_ascii(c: str) -> bool:
    return ("a" <= c <= "z") or ("A" <= c <= "Z")


def eh_digito_ascii(c: str) -> bool:
    return "0" <= c <= "9"


def eh_inicio_identificador(c: str) -> bool:
    return eh_letra_ascii(c) or c == "_"


def eh_parte_identificador(c: str) -> bool:
    return eh_inicio_identificador(c) or eh_digito_ascii(c)


class Lexer:
    def __init__(self, fonte: str):
        self.fonte = fonte
        self.pos = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: list[Token] = []

        self.tokens_codigos: list[int] = []
        self.lexemas: list[str] = []
        self.linhas: list[int] = []

    def _atual(self) -> str:
        return self.fonte[self.pos] if self.pos < len(self.fonte) else "\0"

    def _proximo(self, deslocamento: int = 1) -> str:
        pos = self.pos + deslocamento
        return self.fonte[pos] if pos < len(self.fonte) else "\0"

    def _comeca_com(self, texto: str) -> bool:
        return self.fonte.startswith(texto, self.pos)

    def _avanca(self) -> str:
        c = self._atual()
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    def _avanca_n(self, quantidade: int) -> None:
        for _ in range(quantidade):
            self._avanca()

    def _adiciona_token(self, tipo: TokenType, valor: str, linha: int, coluna: int) -> None:
        token = Token(tipo, valor, linha, coluna)
        self.tokens.append(token)
        self.tokens_codigos.append(tipo.value)
        self.lexemas.append(valor)
        self.linhas.append(linha)

    def _pular_espacos_e_comentarios(self) -> None:
        while self.pos < len(self.fonte):
            c = self._atual()
            if c in (" ", "\t", "\r", "\n"):
                self._avanca()
                continue

            if self._comeca_com("ç#") or self._comeca_com("Ã§#"):
                self._avanca_n(2 if self._comeca_com("ç#") else 3)
                while self.pos < len(self.fonte) and self._atual() != "\n":
                    self._avanca()
                continue

            if self._comeca_com("ç@") or self._comeca_com("Ã§@"):
                linha_inicio = self.linha
                self._avanca_n(2 if self._comeca_com("ç@") else 3)
                fechado = False
                while self.pos < len(self.fonte):
                    if self._comeca_com("@ç"):
                        self._avanca_n(2)
                        fechado = True
                        break
                    if self._comeca_com("@Ã§"):
                        self._avanca_n(3)
                        fechado = True
                        break
                    self._avanca()
                if not fechado:
                    raise ErroLexico(
                        f"Linha {linha_inicio}: comentario de bloco iniciado com 'ç@' nao foi fechado com '@ç'"
                    )
                continue

            break

    def _ler_identificador(self) -> None:
        linha, coluna = self.linha, self.coluna
        lexema = ""
        while eh_parte_identificador(self._atual()):
            lexema += self._avanca()

        if len(lexema) > 64:
            raise ErroLexico(
                f"Linha {linha}: identificador '{lexema[:20]}...' excede o limite de 64 caracteres"
            )

        tipo = KEYWORDS.get(lexema, TokenType.ID)
        self._adiciona_token(tipo, lexema, linha, coluna)

    def _ler_numero(self) -> None:
        linha, coluna = self.linha, self.coluna
        lexema = ""

        while eh_digito_ascii(self._atual()):
            lexema += self._avanca()

        if self._atual() == ".":
            if not eh_digito_ascii(self._proximo()):
                raise ErroLexico(f"Linha {linha}: numero real incompleto em '{lexema}.'")
            lexema += self._avanca()
            while eh_digito_ascii(self._atual()):
                lexema += self._avanca()

        if eh_inicio_identificador(self._atual()) or self._atual().isalpha():
            while eh_parte_identificador(self._atual()) or self._atual().isalpha():
                lexema += self._avanca()
            raise ErroLexico(
                f"Linha {linha}: identificador invalido '{lexema}', identificadores nao podem iniciar com digito"
            )

        self._adiciona_token(TokenType.NUM, lexema, linha, coluna)

    def tokenizar(self) -> tuple[list[int], list[str], list[int]]:
        while self.pos < len(self.fonte):
            self._pular_espacos_e_comentarios()
            if self.pos >= len(self.fonte):
                break

            c = self._atual()
            linha, coluna = self.linha, self.coluna

            if eh_inicio_identificador(c):
                self._ler_identificador()
            elif eh_digito_ascii(c):
                self._ler_numero()
            elif c.isalpha():
                raise ErroLexico(
                    f"Linha {linha}: caractere '{c}' nao e permitido em identificadores da LangC#"
                )
            elif c in ('"', "'", "“", "”"):
                raise ErroLexico(
                    f"Linha {linha}: strings nao fazem parte dos tokens definidos no manual"
                )
            elif c == "=":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.EQ, "==", linha, coluna)
                else:
                    self._adiciona_token(TokenType.ASSIGN, "=", linha, coluna)
            elif c == "!":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.NEQ, "!=", linha, coluna)
                else:
                    raise ErroLexico(f"Linha {linha}: operador invalido '!', esperado '!='")
            elif c == "<":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.LEQ, "<=", linha, coluna)
                else:
                    self._adiciona_token(TokenType.LT, "<", linha, coluna)
            elif c == ">":
                self._avanca()
                if self._atual() == "=":
                    self._avanca()
                    self._adiciona_token(TokenType.GEQ, ">=", linha, coluna)
                else:
                    self._adiciona_token(TokenType.GT, ">", linha, coluna)
            elif c == "+":
                self._avanca()
                self._adiciona_token(TokenType.PLUS, "+", linha, coluna)
            elif c == "-":
                self._avanca()
                self._adiciona_token(TokenType.MINUS, "-", linha, coluna)
            elif c == "*":
                self._avanca()
                self._adiciona_token(TokenType.STAR, "*", linha, coluna)
            elif c == "/":
                self._avanca()
                self._adiciona_token(TokenType.SLASH, "/", linha, coluna)
            elif c == "(":
                self._avanca()
                self._adiciona_token(TokenType.LPAREN, "(", linha, coluna)
            elif c == ")":
                self._avanca()
                self._adiciona_token(TokenType.RPAREN, ")", linha, coluna)
            elif c == "{":
                self._avanca()
                self._adiciona_token(TokenType.LBRACE, "{", linha, coluna)
            elif c == "}":
                self._avanca()
                self._adiciona_token(TokenType.RBRACE, "}", linha, coluna)
            elif c == ",":
                self._avanca()
                self._adiciona_token(TokenType.COMMA, ",", linha, coluna)
            elif c == ";":
                self._avanca()
                self._adiciona_token(TokenType.SEMICOLON, ";", linha, coluna)
            elif c == "ç":
                raise ErroLexico(
                    f"Linha {linha}: marcador de comentario incompleto"
                )
            elif c == "@":
                raise ErroLexico(
                    f"Linha {linha}: operador invalido '@'; '@' isolado nao pertence a linguagem"
                )
            else:
                raise ErroLexico(f"Linha {linha}: caractere inesperado '{c}'")

        self._adiciona_token(TokenType.EOF, "$", self.linha, self.coluna)
        return self.tokens_codigos, self.lexemas, self.linhas


def vetores_para_tokens(tokens_codigos: list[int], lexemas: list[str], linhas: list[int]) -> list[Token]:
    return [
        Token(TokenType(codigo), lexema, linha, 0)
        for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas)
    ]


class Parser:
    EPSILON = "epsilon"

    PRODUCOES = {
        1: ("PROGRAM", ["CONST_DECL_LIST_OPT", "FUNCTION_LIST"]),
        2: ("CONST_DECL_LIST_OPT", ["CONST_DECL", "CONST_DECL_LIST_OPT"]),
        3: ("CONST_DECL_LIST_OPT", []),
        4: ("CONST_DECL", [TokenType.CONST, TokenType.ID, TokenType.ASSIGN, "EXPR", TokenType.SEMICOLON]),
        5: ("FUNCTION_LIST", ["FUNCTION", "FUNCTION_LIST_TAIL"]),
        6: ("FUNCTION_LIST_TAIL", ["FUNCTION", "FUNCTION_LIST_TAIL"]),
        7: ("FUNCTION_LIST_TAIL", []),
        8: ("FUNCTION", ["TYPE", TokenType.ID, TokenType.LPAREN, "PARAM_LIST_OPT", TokenType.RPAREN, "BLOCK"]),
        9: ("TYPE", [TokenType.INT]),
        10: ("TYPE", [TokenType.FLOAT]),
        11: ("PARAM_LIST_OPT", ["PARAM_LIST"]),
        12: ("PARAM_LIST_OPT", []),
        13: ("PARAM_LIST", ["PARAM", "PARAM_LIST_TAIL"]),
        14: ("PARAM_LIST_TAIL", [TokenType.COMMA, "PARAM", "PARAM_LIST_TAIL"]),
        15: ("PARAM_LIST_TAIL", []),
        16: ("PARAM", ["TYPE", TokenType.ID]),
        17: ("BLOCK", [TokenType.LBRACE, "DECL_LIST_OPT", "STMT_LIST_OPT", TokenType.RBRACE]),
        18: ("DECL_LIST_OPT", ["DECL_LIST"]),
        19: ("DECL_LIST_OPT", []),
        20: ("DECL_LIST", ["VAR_DECL", "DECL_LIST_TAIL"]),
        21: ("DECL_LIST_TAIL", ["VAR_DECL", "DECL_LIST_TAIL"]),
        22: ("DECL_LIST_TAIL", []),
        23: ("VAR_DECL", ["TYPE", TokenType.ID, TokenType.SEMICOLON]),
        24: ("STMT_LIST_OPT", ["STMT_LIST"]),
        25: ("STMT_LIST_OPT", []),
        26: ("STMT_LIST", ["STMT", "STMT_LIST_TAIL"]),
        27: ("STMT_LIST_TAIL", ["STMT", "STMT_LIST_TAIL"]),
        28: ("STMT_LIST_TAIL", []),
        29: ("STMT", ["ASSIGN_STMT"]),
        30: ("STMT", ["IF_STMT"]),
        31: ("STMT", ["WHILE_STMT"]),
        32: ("STMT", ["PRINT_STMT"]),
        33: ("STMT", ["RETURN_STMT"]),
        34: ("STMT", ["BLOCK"]),
        35: ("ASSIGN_STMT", [TokenType.ID, TokenType.ASSIGN, "EXPR", TokenType.SEMICOLON]),
        36: ("RETURN_STMT", [TokenType.RETURN, "EXPR", TokenType.SEMICOLON]),
        37: ("PRINT_STMT", [TokenType.PRINT, TokenType.LPAREN, "EXPR", TokenType.RPAREN, TokenType.SEMICOLON]),
        38: ("IF_STMT", [TokenType.IF, TokenType.LPAREN, "EXPR", TokenType.RPAREN, "STMT", "ELSE_PART"]),
        39: ("ELSE_PART", [TokenType.ELSE, "STMT"]),
        40: ("ELSE_PART", []),
        41: ("WHILE_STMT", [TokenType.WHILE, TokenType.LPAREN, "EXPR", TokenType.RPAREN, "STMT"]),
        42: ("EXPR", ["REL_EXPR"]),
        43: ("REL_EXPR", ["ADD_EXPR", "REL_EXPR_TAIL"]),
        44: ("REL_EXPR_TAIL", ["REL_OP", "ADD_EXPR"]),
        45: ("REL_EXPR_TAIL", []),
        46: ("REL_OP", [TokenType.EQ]),
        47: ("REL_OP", [TokenType.NEQ]),
        48: ("REL_OP", [TokenType.LT]),
        49: ("REL_OP", [TokenType.GT]),
        50: ("REL_OP", [TokenType.LEQ]),
        51: ("REL_OP", [TokenType.GEQ]),
        52: ("ADD_EXPR", ["MUL_EXPR", "ADD_EXPR_TAIL"]),
        53: ("ADD_EXPR_TAIL", [TokenType.PLUS, "MUL_EXPR", "ADD_EXPR_TAIL"]),
        54: ("ADD_EXPR_TAIL", [TokenType.MINUS, "MUL_EXPR", "ADD_EXPR_TAIL"]),
        55: ("ADD_EXPR_TAIL", []),
        56: ("MUL_EXPR", ["FACTOR", "MUL_EXPR_TAIL"]),
        57: ("MUL_EXPR_TAIL", [TokenType.STAR, "FACTOR", "MUL_EXPR_TAIL"]),
        58: ("MUL_EXPR_TAIL", [TokenType.SLASH, "FACTOR", "MUL_EXPR_TAIL"]),
        59: ("MUL_EXPR_TAIL", []),
        60: ("FACTOR", [TokenType.LPAREN, "EXPR", TokenType.RPAREN]),
        61: ("FACTOR", [TokenType.ID, "FACTOR_TAIL"]),
        62: ("FACTOR", [TokenType.NUM]),
        63: ("FACTOR_TAIL", [TokenType.LPAREN, "ARG_LIST_OPT", TokenType.RPAREN]),
        64: ("FACTOR_TAIL", []),
        65: ("ARG_LIST_OPT", ["ARG_LIST"]),
        66: ("ARG_LIST_OPT", []),
        67: ("ARG_LIST", ["EXPR", "ARG_LIST_TAIL"]),
        68: ("ARG_LIST_TAIL", [TokenType.COMMA, "EXPR", "ARG_LIST_TAIL"]),
        69: ("ARG_LIST_TAIL", []),
    }

    NAO_TERMINAIS = {esquerda for esquerda, _ in PRODUCOES.values()}
    REL_OPS = {TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LEQ, TokenType.GEQ}
    FIRST_TYPE = {TokenType.INT, TokenType.FLOAT}
    FIRST_STMT = {TokenType.ID, TokenType.IF, TokenType.WHILE, TokenType.PRINT, TokenType.RETURN, TokenType.LBRACE}
    FIRST_EXPR = {TokenType.LPAREN, TokenType.ID, TokenType.NUM}
    FOLLOW_EXPR = {TokenType.RPAREN, TokenType.SEMICOLON, TokenType.COMMA}
    FOLLOW_FACTOR = FOLLOW_EXPR | REL_OPS | {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.tabela = self._criar_tabela()
        self.passos: list[PassoSintatico] = []

    @property
    def atual(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    @classmethod
    def _criar_tabela(cls) -> dict[tuple[str, TokenType], int]:
        tabela: dict[tuple[str, TokenType], int] = {}

        def add(nao_terminal: str, terminais: set[TokenType], producao: int) -> None:
            for terminal in terminais:
                tabela[(nao_terminal, terminal)] = producao

        add("PROGRAM", {TokenType.CONST} | cls.FIRST_TYPE, 1)
        add("CONST_DECL_LIST_OPT", {TokenType.CONST}, 2)
        add("CONST_DECL_LIST_OPT", cls.FIRST_TYPE, 3)
        add("CONST_DECL", {TokenType.CONST}, 4)
        add("FUNCTION_LIST", cls.FIRST_TYPE, 5)
        add("FUNCTION_LIST_TAIL", cls.FIRST_TYPE, 6)
        add("FUNCTION_LIST_TAIL", {TokenType.EOF}, 7)
        add("FUNCTION", cls.FIRST_TYPE, 8)
        add("TYPE", {TokenType.INT}, 9)
        add("TYPE", {TokenType.FLOAT}, 10)
        add("PARAM_LIST_OPT", cls.FIRST_TYPE, 11)
        add("PARAM_LIST_OPT", {TokenType.RPAREN}, 12)
        add("PARAM_LIST", cls.FIRST_TYPE, 13)
        add("PARAM_LIST_TAIL", {TokenType.COMMA}, 14)
        add("PARAM_LIST_TAIL", {TokenType.RPAREN}, 15)
        add("PARAM", cls.FIRST_TYPE, 16)
        add("BLOCK", {TokenType.LBRACE}, 17)
        add("DECL_LIST_OPT", cls.FIRST_TYPE, 18)
        add("DECL_LIST_OPT", cls.FIRST_STMT | {TokenType.RBRACE}, 19)
        add("DECL_LIST", cls.FIRST_TYPE, 20)
        add("DECL_LIST_TAIL", cls.FIRST_TYPE, 21)
        add("DECL_LIST_TAIL", cls.FIRST_STMT | {TokenType.RBRACE}, 22)
        add("VAR_DECL", cls.FIRST_TYPE, 23)
        add("STMT_LIST_OPT", cls.FIRST_STMT, 24)
        add("STMT_LIST_OPT", {TokenType.RBRACE}, 25)
        add("STMT_LIST", cls.FIRST_STMT, 26)
        add("STMT_LIST_TAIL", cls.FIRST_STMT, 27)
        add("STMT_LIST_TAIL", {TokenType.RBRACE}, 28)
        add("STMT", {TokenType.ID}, 29)
        add("STMT", {TokenType.IF}, 30)
        add("STMT", {TokenType.WHILE}, 31)
        add("STMT", {TokenType.PRINT}, 32)
        add("STMT", {TokenType.RETURN}, 33)
        add("STMT", {TokenType.LBRACE}, 34)
        add("ASSIGN_STMT", {TokenType.ID}, 35)
        add("RETURN_STMT", {TokenType.RETURN}, 36)
        add("PRINT_STMT", {TokenType.PRINT}, 37)
        add("IF_STMT", {TokenType.IF}, 38)
        add("ELSE_PART", {TokenType.ELSE}, 39)
        add("ELSE_PART", cls.FIRST_STMT | {TokenType.RBRACE, TokenType.EOF}, 40)
        add("WHILE_STMT", {TokenType.WHILE}, 41)
        add("EXPR", cls.FIRST_EXPR, 42)
        add("REL_EXPR", cls.FIRST_EXPR, 43)
        add("REL_EXPR_TAIL", cls.REL_OPS, 44)
        add("REL_EXPR_TAIL", cls.FOLLOW_EXPR, 45)
        add("REL_OP", {TokenType.EQ}, 46)
        add("REL_OP", {TokenType.NEQ}, 47)
        add("REL_OP", {TokenType.LT}, 48)
        add("REL_OP", {TokenType.GT}, 49)
        add("REL_OP", {TokenType.LEQ}, 50)
        add("REL_OP", {TokenType.GEQ}, 51)
        add("ADD_EXPR", cls.FIRST_EXPR, 52)
        add("ADD_EXPR_TAIL", {TokenType.PLUS}, 53)
        add("ADD_EXPR_TAIL", {TokenType.MINUS}, 54)
        add("ADD_EXPR_TAIL", cls.REL_OPS | cls.FOLLOW_EXPR, 55)
        add("MUL_EXPR", cls.FIRST_EXPR, 56)
        add("MUL_EXPR_TAIL", {TokenType.STAR}, 57)
        add("MUL_EXPR_TAIL", {TokenType.SLASH}, 58)
        add("MUL_EXPR_TAIL", {TokenType.PLUS, TokenType.MINUS} | cls.REL_OPS | cls.FOLLOW_EXPR, 59)
        add("FACTOR", {TokenType.LPAREN}, 60)
        add("FACTOR", {TokenType.ID}, 61)
        add("FACTOR", {TokenType.NUM}, 62)
        add("FACTOR_TAIL", {TokenType.LPAREN}, 63)
        add("FACTOR_TAIL", cls.FOLLOW_FACTOR, 64)
        add("ARG_LIST_OPT", cls.FIRST_EXPR, 65)
        add("ARG_LIST_OPT", {TokenType.RPAREN}, 66)
        add("ARG_LIST", cls.FIRST_EXPR, 67)
        add("ARG_LIST_TAIL", {TokenType.COMMA}, 68)
        add("ARG_LIST_TAIL", {TokenType.RPAREN}, 69)
        return tabela

    def _formatar_simbolo(self, simbolo) -> str:
        if isinstance(simbolo, TokenType):
            return TOKEN_TEXT[simbolo]
        return str(simbolo)

    def _formatar_pilha(self, pilha: list[TokenType | str]) -> str:
        return " ".join(self._formatar_simbolo(s) for s in reversed(pilha))

    def _formatar_producao(self, numero: int) -> str:
        esquerda, direita = self.PRODUCOES[numero]
        texto = " ".join(self._formatar_simbolo(s) for s in direita) if direita else self.EPSILON
        return f"{esquerda} -> {texto}"

    def _registrar(self, passo: int, pilha: list[TokenType | str], tok: Token, acao: str) -> None:
        self.passos.append(
            PassoSintatico(
                passo=passo,
                codigo_token=tok.tipo.value,
                token=tok.tipo.name,
                lexema=tok.valor,
                linha=tok.linha,
                pilha=self._formatar_pilha(pilha),
                acao=acao,
            )
        )

    def _token_encontrado(self, tok: Token) -> str:
        if tok.tipo == TokenType.EOF:
            return "fim de entrada '$'"
        return f"{tok.valor!r}"

    def _erro_terminal(self, esperado: TokenType, encontrado: Token) -> str:
        anterior = self.tokens[self.pos - 1] if self.pos > 0 else encontrado
        if esperado == TokenType.SEMICOLON:
            return (
                f"Linha {anterior.linha}: faltou ';' ao final da instrucao antes de "
                f"{self._token_encontrado(encontrado)}"
            )
        if esperado == TokenType.RPAREN:
            return f"Linha {anterior.linha}: faltou ')' antes de {self._token_encontrado(encontrado)}"
        if esperado == TokenType.RBRACE:
            return f"Linha {anterior.linha}: faltou '}}' antes de {self._token_encontrado(encontrado)}"
        if esperado == TokenType.ID and anterior.tipo in self.FIRST_TYPE:
            return (
                f"Linha {encontrado.linha}: esperado identificador apos o tipo "
                f"{self._token_encontrado(anterior)}, encontrado {self._token_encontrado(encontrado)}"
            )
        return (
            f"Linha {encontrado.linha}: esperado '{TOKEN_TEXT[esperado]}', "
            f"encontrado {self._token_encontrado(encontrado)}"
        )

    def _erro_tabela(self, nao_terminal: str, encontrado: Token) -> str:
        esperados = sorted(
            TOKEN_TEXT[terminal]
            for nt, terminal in self.tabela
            if nt == nao_terminal
        )
        return (
            f"Linha {encontrado.linha}: erro sintatico em {nao_terminal}; "
            f"encontrado {self._token_encontrado(encontrado)}. "
            f"Esperado um de: {', '.join(esperados)}"
        )

    def programa(self) -> list[PassoSintatico]:
        pilha: list[TokenType | str] = [TokenType.EOF, "PROGRAM"]
        passo = 1

        while pilha:
            topo = pilha[-1]
            tok = self.atual

            if isinstance(topo, TokenType):
                if topo != tok.tipo:
                    raise ErroSintatico(self._erro_terminal(topo, tok))
                self._registrar(passo, pilha, tok, f"Consome {TOKEN_TEXT[topo]}")
                pilha.pop()
                self.pos += 1
                passo += 1
                continue

            numero_producao = self.tabela.get((topo, tok.tipo))
            if numero_producao is None:
                raise ErroSintatico(self._erro_tabela(topo, tok))

            self._registrar(
                passo,
                pilha,
                tok,
                f"Usa {numero_producao}: {self._formatar_producao(numero_producao)}",
            )
            pilha.pop()
            _, direita = self.PRODUCOES[numero_producao]
            for simbolo in reversed(direita):
                pilha.append(simbolo)
            passo += 1

        return self.passos


class AnalisadorSemantico:
    FIRST_STMT = {TokenType.ID, TokenType.IF, TokenType.WHILE, TokenType.PRINT, TokenType.RETURN, TokenType.LBRACE}

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.simbolos: list[Simbolo] = []
        self.eventos: list[EventoSemantico] = []
        self.escopos: list[dict[str, Simbolo]] = [{}]
        self.funcoes_listadas: set[str] = set()
        self.funcao_atual: Simbolo | None = None
        self.nivel_atual = 0

    @property
    def atual(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def anterior(self) -> Token:
        return self.tokens[self.pos - 1]

    def registrar(self, etapa: str, detalhe: str, linha: int | None = None, status: str = "OK") -> None:
        self.eventos.append(EventoSemantico(len(self.eventos) + 1, etapa, detalhe, linha, status))

    def erro(self, mensagem: str, token: Token, etapa: str = "Erro semantico") -> None:
        self.registrar(etapa, mensagem, token.linha, "ERRO")
        raise ErroSemantico(f"Linha {token.linha}: {mensagem}")

    def check(self, tipo: TokenType) -> bool:
        return self.atual.tipo == tipo

    def match(self, *tipos: TokenType) -> bool:
        if self.atual.tipo in tipos:
            self.pos += 1
            return True
        return False

    def consumir(self, tipo: TokenType, mensagem: str) -> Token:
        if self.atual.tipo == tipo:
            self.pos += 1
            return self.tokens[self.pos - 1]
        raise ErroSintatico(f"Linha {self.atual.linha}: {mensagem}, encontrado {self.atual.valor!r}")

    def tipo_texto(self, token_tipo: TokenType) -> str:
        if token_tipo == TokenType.INT:
            return "int"
        if token_tipo == TokenType.FLOAT:
            return "float"
        return token_tipo.name.lower()

    def procurar(self, nome: str) -> Simbolo | None:
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

    def declarar(self, simbolo: Simbolo, token_nome: Token, permitir_predeclarado: bool = False) -> Simbolo:
        escopo_atual = self.escopos[-1]

        if token_nome.valor in escopo_atual and not permitir_predeclarado:
            self.erro(f"identificador '{token_nome.valor}' ja declarado neste escopo", token_nome)

        global_existente = self.escopos[0].get(token_nome.valor)
        if self.nivel_atual > 0 and global_existente and global_existente.categoria in {"constante", "funcao"}:
            self.erro(
                f"identificador '{token_nome.valor}' ja usado no escopo global como {global_existente.categoria}",
                token_nome,
            )

        escopo_atual[token_nome.valor] = simbolo
        self.simbolos.append(simbolo)
        return simbolo

    def predeclarar_funcoes(self) -> None:
        pos = 0
        while self.tokens[pos].tipo == TokenType.CONST:
            while self.tokens[pos].tipo not in (TokenType.SEMICOLON, TokenType.EOF):
                pos += 1
            if self.tokens[pos].tipo == TokenType.SEMICOLON:
                pos += 1

        while self.tokens[pos].tipo != TokenType.EOF:
            if (
                self.tokens[pos].tipo in (TokenType.INT, TokenType.FLOAT)
                and self.tokens[pos + 1].tipo == TokenType.ID
                and self.tokens[pos + 2].tipo == TokenType.LPAREN
            ):
                tipo_funcao = self.tipo_texto(self.tokens[pos].tipo)
                nome_token = self.tokens[pos + 1]
                parametros: list[str] = []
                p = pos + 3
                while self.tokens[p].tipo != TokenType.RPAREN:
                    if self.tokens[p].tipo in (TokenType.INT, TokenType.FLOAT):
                        parametros.append(self.tipo_texto(self.tokens[p].tipo))
                        p += 2
                        if self.tokens[p].tipo == TokenType.COMMA:
                            p += 1
                        continue
                    p += 1

                if nome_token.valor in self.escopos[0]:
                    self.erro(f"funcao '{nome_token.valor}' ja declarada", nome_token)

                self.escopos[0][nome_token.valor] = Simbolo(
                    nome=nome_token.valor,
                    categoria="funcao",
                    tipo=tipo_funcao,
                    nivel=0,
                    linha=nome_token.linha,
                    escopo="global",
                    parametros=parametros,
                )

                pos = p + 1
                if self.tokens[pos].tipo == TokenType.LBRACE:
                    profundidade = 0
                    while self.tokens[pos].tipo != TokenType.EOF:
                        if self.tokens[pos].tipo == TokenType.LBRACE:
                            profundidade += 1
                        elif self.tokens[pos].tipo == TokenType.RBRACE:
                            profundidade -= 1
                            if profundidade == 0:
                                pos += 1
                                break
                        pos += 1
                continue

            pos += 1

    def analisar(self) -> tuple[list[Simbolo], list[EventoSemantico]]:
        self.registrar(
            "Preparar tabela",
            "Criada a tabela de simbolos com Nome, Categoria, Tipo e Nivel, conforme AcoesSemantico.pdf.",
        )
        self.predeclarar_funcoes()
        self.programa()
        self.registrar("Resultado", "Analise semantica concluida sem erros.", status="OK")
        return self.simbolos, self.eventos

    def programa(self) -> None:
        while self.match(TokenType.CONST):
            self.declaracao_constante(self.anterior())

        while not self.check(TokenType.EOF):
            self.funcao()

        self.consumir(TokenType.EOF, "esperado fim de entrada")

    def declaracao_constante(self, token_const: Token) -> None:
        self.registrar(
            "Encontrar const",
            "Token 'const' encontrado no nivel global; const + 1 deve apontar para o nome.",
            token_const.linha,
        )
        nome_token = self.consumir(TokenType.ID, "esperado nome da constante apos 'const'")
        self.consumir(TokenType.ASSIGN, "esperado '=' na declaracao de constante")
        token_valor = self.atual
        tipo = self.expressao()
        self.consumir(TokenType.SEMICOLON, "esperado ';' ao final da constante")

        if nome_token.valor in self.escopos[0]:
            self.erro(f"identificador global '{nome_token.valor}' ja declarado", nome_token)

        simbolo = Simbolo(nome_token.valor, "constante", tipo, 0, nome_token.linha, "global")
        self.escopos[0][nome_token.valor] = simbolo
        self.simbolos.append(simbolo)

        self.registrar(
            "Inferir tipo",
            f"const + 3 inicia em '{token_valor.valor}'; o tipo registrado para '{nome_token.valor}' e {tipo}.",
            token_valor.linha,
        )
        self.registrar(
            "Inserir simbolo",
            f"Inserido Nome={simbolo.nome}, Categoria=constante, Tipo={simbolo.tipo}, Nivel=0.",
            nome_token.linha,
        )

    def tipo(self) -> str:
        if self.match(TokenType.INT):
            return "int"
        if self.match(TokenType.FLOAT):
            return "float"
        raise ErroSintatico(f"Linha {self.atual.linha}: esperado tipo int ou float")

    def funcao(self) -> None:
        tipo_retorno = self.tipo()
        nome_token = self.consumir(TokenType.ID, "esperado nome da funcao")
        simbolo_funcao = self.escopos[0].get(nome_token.valor)
        if simbolo_funcao is None or simbolo_funcao.categoria != "funcao":
            self.erro(f"funcao '{nome_token.valor}' nao foi registrada corretamente", nome_token)

        if nome_token.valor not in self.funcoes_listadas:
            self.simbolos.append(simbolo_funcao)
            self.funcoes_listadas.add(nome_token.valor)
            self.registrar(
                "Declarar funcao",
                f"Funcao '{nome_token.valor}' registrada no nivel 0 com retorno {tipo_retorno}.",
                nome_token.linha,
            )

        self.consumir(TokenType.LPAREN, "esperado '(' apos nome da funcao")
        escopo_funcao: dict[str, Simbolo] = {}
        self.escopos.append(escopo_funcao)
        self.nivel_atual = 1
        funcao_anterior = self.funcao_atual
        self.funcao_atual = simbolo_funcao

        indice_parametro = 0
        if not self.check(TokenType.RPAREN):
            while True:
                tipo_parametro = self.tipo()
                nome_parametro = self.consumir(TokenType.ID, "esperado nome do parametro")
                simbolo_parametro = Simbolo(
                    nome_parametro.valor,
                    "parametro",
                    tipo_parametro,
                    1,
                    nome_parametro.linha,
                    nome_token.valor,
                )
                self.declarar(simbolo_parametro, nome_parametro)
                self.registrar(
                    "Declarar parametro",
                    f"Parametro '{nome_parametro.valor}' registrado no nivel 1 com tipo {tipo_parametro}.",
                    nome_parametro.linha,
                )
                indice_parametro += 1
                if not self.match(TokenType.COMMA):
                    break

        if indice_parametro != len(simbolo_funcao.parametros):
            self.erro(f"assinatura inconsistente para funcao '{nome_token.valor}'", nome_token)

        self.consumir(TokenType.RPAREN, "esperado ')' apos parametros")
        self.bloco(criar_escopo=False, nome_escopo=nome_token.valor)

        self.escopos.pop()
        self.nivel_atual = 0
        self.funcao_atual = funcao_anterior

    def bloco(self, criar_escopo: bool, nome_escopo: str) -> None:
        self.consumir(TokenType.LBRACE, "esperado '{' no inicio do bloco")

        if criar_escopo:
            self.escopos.append({})
            self.nivel_atual += 1

        while self.atual.tipo in (TokenType.INT, TokenType.FLOAT):
            self.declaracao_variavel(nome_escopo)

        while self.atual.tipo in self.FIRST_STMT:
            self.comando(nome_escopo)

        self.consumir(TokenType.RBRACE, "esperado '}' no final do bloco")

        if criar_escopo:
            self.escopos.pop()
            self.nivel_atual -= 1

    def declaracao_variavel(self, nome_escopo: str) -> None:
        tipo_variavel = self.tipo()
        nome_token = self.consumir(TokenType.ID, "esperado nome da variavel")
        self.consumir(TokenType.SEMICOLON, "esperado ';' apos declaracao de variavel")

        simbolo = Simbolo(
            nome_token.valor,
            "variavel",
            tipo_variavel,
            self.nivel_atual,
            nome_token.linha,
            nome_escopo,
        )
        self.declarar(simbolo, nome_token)
        self.registrar(
            "Declarar variavel",
            f"Variavel '{nome_token.valor}' registrada no nivel {self.nivel_atual} com tipo {tipo_variavel}.",
            nome_token.linha,
        )

    def comando(self, nome_escopo: str) -> None:
        if self.check(TokenType.ID):
            self.atribuicao()
        elif self.match(TokenType.RETURN):
            self.retorno(self.anterior())
        elif self.match(TokenType.PRINT):
            self.print_stmt(self.anterior())
        elif self.match(TokenType.IF):
            self.if_stmt(nome_escopo, self.anterior())
        elif self.match(TokenType.WHILE):
            self.while_stmt(nome_escopo, self.anterior())
        elif self.check(TokenType.LBRACE):
            self.bloco(criar_escopo=True, nome_escopo=nome_escopo)
        else:
            raise ErroSintatico(f"Linha {self.atual.linha}: comando invalido")

    def atribuicao(self) -> None:
        nome_token = self.consumir(TokenType.ID, "esperado identificador na atribuicao")
        simbolo = self.procurar(nome_token.valor)
        self.registrar(
            "Consultar tabela",
            f"Token '{nome_token.valor}' antes de '='; consultar categoria na tabela de simbolos.",
            nome_token.linha,
        )

        if simbolo is None:
            self.erro(f"identificador '{nome_token.valor}' usado antes da declaracao", nome_token)
        if simbolo.categoria == "constante":
            self.registrar(
                "Erro semantico",
                f"'{nome_token.valor}' esta como constante; o proximo token da pilha nao pode ser '='.",
                nome_token.linha,
                "ERRO",
            )
            raise ErroSemantico(
                f"Linha {nome_token.linha}: o valor da constante '{nome_token.valor}' nao pode ser alterado"
            )
        if simbolo.categoria == "funcao":
            self.erro(f"funcao '{nome_token.valor}' nao pode receber atribuicao", nome_token)

        self.consumir(TokenType.ASSIGN, "esperado '=' na atribuicao")
        tipo_expr = self.expressao()
        self.consumir(TokenType.SEMICOLON, "esperado ';' apos atribuicao")

        self.exigir_tipos_iguais(simbolo.tipo, tipo_expr, nome_token, f"atribuicao para '{nome_token.valor}'")
        self.registrar(
            "Checar atribuicao",
            f"Atribuicao para '{nome_token.valor}' permitida: {simbolo.tipo} recebe {tipo_expr}.",
            nome_token.linha,
        )

    def retorno(self, token_return: Token) -> None:
        tipo_expr = self.expressao()
        self.consumir(TokenType.SEMICOLON, "esperado ';' apos return")
        if self.funcao_atual is None:
            self.erro("'return' fora de funcao", token_return)
        self.exigir_tipos_iguais(self.funcao_atual.tipo, tipo_expr, token_return, "return")
        self.registrar(
            "Checar return",
            f"Return da funcao '{self.funcao_atual.nome}' compativel: {self.funcao_atual.tipo}.",
            token_return.linha,
        )

    def print_stmt(self, token_print: Token) -> None:
        self.consumir(TokenType.LPAREN, "esperado '(' apos print")
        tipo_expr = self.expressao()
        self.consumir(TokenType.RPAREN, "esperado ')' apos expressao do print")
        self.consumir(TokenType.SEMICOLON, "esperado ';' apos print")
        self.registrar("Checar print", f"print recebe expressao do tipo {tipo_expr}.", token_print.linha)

    def if_stmt(self, nome_escopo: str, token_if: Token) -> None:
        self.consumir(TokenType.LPAREN, "esperado '(' apos if")
        tipo_condicao = self.expressao()
        self.consumir(TokenType.RPAREN, "esperado ')' apos condicao do if")
        self.registrar("Checar if", f"Condicao do if possui tipo {tipo_condicao}.", token_if.linha)
        self.comando(nome_escopo)
        if self.match(TokenType.ELSE):
            self.comando(nome_escopo)

    def while_stmt(self, nome_escopo: str, token_while: Token) -> None:
        self.consumir(TokenType.LPAREN, "esperado '(' apos while")
        tipo_condicao = self.expressao()
        self.consumir(TokenType.RPAREN, "esperado ')' apos condicao do while")
        self.registrar("Checar while", f"Condicao do while possui tipo {tipo_condicao}.", token_while.linha)
        self.comando(nome_escopo)

    def expressao(self) -> str:
        return self.relacional()

    def relacional(self) -> str:
        tipo_esq = self.aditivo()
        if self.atual.tipo in Parser.REL_OPS:
            operador = self.atual
            self.pos += 1
            tipo_dir = self.aditivo()
            self.exigir_tipos_iguais(tipo_esq, tipo_dir, operador, f"operador relacional {operador.valor}")
            self.registrar(
                "Checar expressao",
                f"Operador relacional '{operador.valor}' aplicado a {tipo_esq}; resultado tratado como int.",
                operador.linha,
            )
            return "int"
        return tipo_esq

    def aditivo(self) -> str:
        tipo = self.multiplicativo()
        while self.atual.tipo in (TokenType.PLUS, TokenType.MINUS):
            operador = self.atual
            self.pos += 1
            tipo_dir = self.multiplicativo()
            self.exigir_tipos_iguais(tipo, tipo_dir, operador, f"operador aritmetico {operador.valor}")
            self.registrar(
                "Checar expressao",
                f"Operador '{operador.valor}' aplicado a operandos {tipo}.",
                operador.linha,
            )
        return tipo

    def multiplicativo(self) -> str:
        tipo = self.fator()
        while self.atual.tipo in (TokenType.STAR, TokenType.SLASH):
            operador = self.atual
            self.pos += 1
            tipo_dir = self.fator()
            self.exigir_tipos_iguais(tipo, tipo_dir, operador, f"operador aritmetico {operador.valor}")
            self.registrar(
                "Checar expressao",
                f"Operador '{operador.valor}' aplicado a operandos {tipo}.",
                operador.linha,
            )
        return tipo

    def fator(self) -> str:
        if self.match(TokenType.NUM):
            token = self.anterior()
            return "float" if "." in token.valor else "int"

        if self.match(TokenType.LPAREN):
            tipo = self.expressao()
            self.consumir(TokenType.RPAREN, "esperado ')' apos expressao")
            return tipo

        if self.match(TokenType.ID):
            nome_token = self.anterior()
            if self.match(TokenType.LPAREN):
                return self.chamada_funcao(nome_token)

            simbolo = self.procurar(nome_token.valor)
            if simbolo is None:
                self.erro(f"identificador '{nome_token.valor}' usado antes da declaracao", nome_token)
            if simbolo.categoria == "funcao":
                self.erro(f"funcao '{nome_token.valor}' deve ser chamada com parenteses", nome_token)

            self.registrar(
                "Consultar tabela",
                f"Uso de '{nome_token.valor}' encontrado como {simbolo.categoria} do tipo {simbolo.tipo}.",
                nome_token.linha,
            )
            return simbolo.tipo

        raise ErroSintatico(f"Linha {self.atual.linha}: esperado fator em expressao")

    def chamada_funcao(self, nome_token: Token) -> str:
        simbolo = self.escopos[0].get(nome_token.valor)
        if simbolo is None or simbolo.categoria != "funcao":
            self.erro(f"funcao '{nome_token.valor}' nao declarada", nome_token)

        tipos_argumentos: list[str] = []
        if not self.check(TokenType.RPAREN):
            while True:
                tipos_argumentos.append(self.expressao())
                if not self.match(TokenType.COMMA):
                    break

        self.consumir(TokenType.RPAREN, "esperado ')' apos argumentos")

        if len(tipos_argumentos) != len(simbolo.parametros):
            self.erro(
                f"funcao '{nome_token.valor}' espera {len(simbolo.parametros)} argumento(s), "
                f"mas recebeu {len(tipos_argumentos)}",
                nome_token,
            )

        for indice, (esperado, recebido) in enumerate(zip(simbolo.parametros, tipos_argumentos), start=1):
            if esperado != recebido:
                self.erro(
                    f"argumento {indice} de '{nome_token.valor}' espera {esperado}, recebeu {recebido}",
                    nome_token,
                )

        self.registrar(
            "Checar chamada",
            f"Chamada de '{nome_token.valor}' validada com retorno {simbolo.tipo}.",
            nome_token.linha,
        )
        return simbolo.tipo

    def exigir_tipos_iguais(self, esperado: str, recebido: str, token: Token, contexto: str) -> None:
        if esperado != recebido:
            self.erro(
                f"tipos incompativeis em {contexto}: esperado {esperado}, recebido {recebido}",
                token,
                etapa="Erro de tipo",
            )


REQUISITOS_PDF = [
    [
        "Manual LangC#",
        "Programa formado por funcoes tipadas; variaveis declaradas no inicio do bloco.",
        "Parser LL(1) valida funcoes, parametros, blocos, declaracoes e comandos nessa ordem.",
    ],
    [
        "Manual LangC#",
        "Identificadores ASCII com ate 64 caracteres; numeros inteiros/reais; comentarios ç# e ç@...@ç.",
        "Lexer implementa cada regra e aponta linha no erro lexico.",
    ],
    [
        "Manual LangC#",
        "Sem conversao implicita entre int e float.",
        "Semantico compara tipos em atribuicao, return, operadores e chamadas.",
    ],
    [
        "AcoesSemantico.pdf",
        "Tabela de simbolos com Nome, Categoria, Tipo e Nivel.",
        "Relatorio mostra a tabela completa com constantes, funcoes, parametros e variaveis.",
    ],
    [
        "AcoesSemantico.pdf",
        "Inserir const global como Categoria constante e Nivel 0.",
        "Declaracoes const antes das funcoes entram como simbolos globais.",
    ],
    [
        "AcoesSemantico.pdf",
        "Valor de const nao pode ser alterado; mostrar linha e erro semantico.",
        "Atribuicao para simbolo constante gera ErroSemantico com linha.",
    ],
]


def compilar_codigo(codigo: str, origem: str = "entrada direta") -> ResultadoCompilacao:
    resultado = ResultadoCompilacao(origem=origem, codigo=codigo)

    try:
        lexer = Lexer(codigo)
        lexer.tokenizar()
        resultado.tokens = lexer.tokens
        resultado.fase = "lexica"
    except ErroLexico as erro:
        resultado.diagnostico = str(erro)
        resultado.fase = "lexica"
        return resultado

    try:
        parser = Parser(resultado.tokens)
        resultado.passos_sintaticos = parser.programa()
        resultado.fase = "sintatica"
    except ErroSintatico as erro:
        resultado.diagnostico = str(erro)
        resultado.fase = "sintatica"
        return resultado

    try:
        semantico = AnalisadorSemantico(resultado.tokens)
        resultado.simbolos, resultado.eventos_semanticos = semantico.analisar()
        resultado.fase = "semantica"
    except ErroSemantico as erro:
        resultado.simbolos = semantico.simbolos
        resultado.eventos_semanticos = semantico.eventos
        resultado.diagnostico = str(erro)
        resultado.fase = "semantica"
        return resultado
    except ErroSintatico as erro:
        resultado.simbolos = semantico.simbolos
        resultado.eventos_semanticos = semantico.eventos
        resultado.diagnostico = str(erro)
        resultado.fase = "semantica"
        return resultado

    resultado.sucesso = True
    resultado.diagnostico = "Compilacao concluida sem erros lexicos, sintaticos ou semanticos."
    return resultado


def ler_arquivo(caminho: Path) -> str:
    try:
        return caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Arquivo '{caminho}' nao esta em UTF-8 valido.") from exc
    except OSError as exc:
        raise RuntimeError(f"Erro ao ler '{caminho}': {exc}") from exc


def nome_relatorio(origem: str) -> str:
    stem = Path(origem).stem if origem != "entrada direta" else "entrada_direta"
    seguro = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in stem)
    return f"{seguro}_relatorio.html"


def exportar_tokens_json(resultado: ResultadoCompilacao, caminho_entrada: Path | None = None) -> Path | None:
    if not resultado.tokens:
        return None

    PASTA_TOKENS.mkdir(parents=True, exist_ok=True)
    if caminho_entrada is not None:
        caminho = PASTA_TOKENS / f"{caminho_entrada.stem}_tokens.json"
    else:
        caminho = PASTA_TOKENS / "entrada_direta_tokens.json"

    tokens_sem_eof = [token for token in resultado.tokens if token.tipo != TokenType.EOF]
    dados = {
        "tokens": [token.tipo.value for token in tokens_sem_eof],
        "lexemas": [token.valor for token in tokens_sem_eof],
        "linhas": [token.linha for token in tokens_sem_eof],
        "detalhes": [
            {
                "codigo": token.tipo.value,
                "token": token.tipo.name,
                "lexema": token.valor,
                "linha": token.linha,
                "coluna": token.coluna,
            }
            for token in tokens_sem_eof
        ],
    }
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    resultado.json_tokens = caminho
    return caminho


def html_escape(valor) -> str:
    return html.escape(str(valor), quote=True)


def html_tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    head = "".join(f"<th>{html_escape(coluna)}</th>" for coluna in cabecalho)
    if not linhas:
        body = f"<tr><td colspan=\"{len(cabecalho)}\">Nenhum registro.</td></tr>"
    else:
        body = "".join(
            "<tr>" + "".join(f"<td>{html_escape(valor)}</td>" for valor in linha) + "</tr>"
            for linha in linhas
        )

    return (
        "<div class=\"table-wrap\"><table>"
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )


def html_codigo(codigo: str) -> str:
    linhas = codigo.splitlines() or [""]
    itens = []
    for numero, linha in enumerate(linhas, start=1):
        itens.append(
            "<div class=\"code-line\">"
            f"<span>{numero}</span><code>{html_escape(linha)}</code>"
            "</div>"
        )
    return f"<div class=\"code-box\">{''.join(itens)}</div>"


def linhas_tokens(tokens: list[Token]) -> list[list[str]]:
    return [
        [str(i), str(t.tipo.value), t.tipo.name, t.valor, str(t.linha), str(t.coluna)]
        for i, t in enumerate(tokens, start=1)
        if t.tipo != TokenType.EOF
    ]


def linhas_passos(passos: list[PassoSintatico]) -> list[list[str]]:
    return [
        [
            str(p.passo),
            str(p.codigo_token),
            p.token,
            p.lexema,
            str(p.linha),
            p.pilha,
            p.acao,
        ]
        for p in passos
    ]


def linhas_simbolos(simbolos: list[Simbolo]) -> list[list[str]]:
    return [
        [
            str(i),
            s.nome,
            s.categoria,
            s.tipo,
            str(s.nivel),
            str(s.linha),
            s.escopo,
            ", ".join(s.parametros),
        ]
        for i, s in enumerate(simbolos, start=1)
    ]


def linhas_eventos(eventos: list[EventoSemantico]) -> list[list[str]]:
    return [
        [
            str(e.passo),
            e.etapa,
            e.detalhe,
            "" if e.linha is None else str(e.linha),
            e.status,
        ]
        for e in eventos
    ]


def gerar_relatorio_html(resultado: ResultadoCompilacao, caminho: Path | None = None) -> Path:
    PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)
    caminho = caminho or (PASTA_RELATORIOS / nome_relatorio(resultado.origem))
    status_classe = "ok" if resultado.sucesso else "erro"
    status_texto = "OK" if resultado.sucesso else "ERRO"

    tokens_count = len([t for t in resultado.tokens if t.tipo != TokenType.EOF])
    diagnostico_classe = "panel ok-panel" if resultado.sucesso else "panel error-panel"

    documento = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Compilador LangC# - {html_escape(resultado.origem)}</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --surface: #ffffff;
      --ink: #18212a;
      --muted: #62707f;
      --line: #d8e0e7;
      --accent: #176b87;
      --accent-2: #2f6f5e;
      --warn: #b84838;
      --ok: #227252;
      --soft-blue: #e8f2f6;
      --soft-green: #e5f4ed;
      --soft-red: #fde9e5;
      --soft-yellow: #fff3d8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-width: 320px;
      background: var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", Arial, sans-serif;
      line-height: 1.5;
    }}
    header {{
      background: #17242d;
      color: #f8fbfc;
      border-bottom: 5px solid var(--accent);
    }}
    .wrap {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }}
    .hero {{
      min-height: 210px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      padding: 34px 0 28px;
    }}
    .eyebrow {{
      color: #9bd3df;
      font-size: .78rem;
      font-weight: 800;
      text-transform: uppercase;
    }}
    h1, h2, h3, p {{ margin: 0; }}
    h1 {{
      margin-top: 8px;
      font-size: clamp(2rem, 4vw, 3.7rem);
      line-height: 1;
      letter-spacing: 0;
    }}
    .file {{
      margin-top: 12px;
      color: #cbd9df;
      font-family: Consolas, "Courier New", monospace;
      overflow-wrap: anywhere;
    }}
    .badge {{
      min-width: 128px;
      border-radius: 8px;
      padding: 14px 16px;
      text-align: center;
      font-weight: 900;
      background: var(--soft-green);
      color: var(--ok);
    }}
    .badge.erro {{
      background: var(--soft-red);
      color: var(--warn);
    }}
    main {{ padding: 24px 0 44px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .metric, .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 14px 32px rgba(24, 33, 42, .08);
    }}
    .metric {{ min-height: 86px; padding: 15px; }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: .76rem;
      font-weight: 800;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      margin-top: 6px;
      font-size: 1.42rem;
      overflow-wrap: anywhere;
    }}
    .panel {{
      padding: 18px;
      margin-bottom: 18px;
      overflow: hidden;
    }}
    .panel h2 {{ margin-bottom: 12px; font-size: 1.14rem; }}
    .error-panel {{ background: var(--soft-red); border-color: #e8afa8; }}
    .ok-panel {{ background: var(--soft-green); border-color: #add9c6; }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, .92fr) minmax(0, 1.08fr);
      gap: 18px;
      align-items: start;
    }}
    .code-box {{
      max-height: 580px;
      overflow: auto;
      border-radius: 8px;
      background: #101820;
      color: #edf5f3;
      font-family: Consolas, "Courier New", monospace;
      font-size: .92rem;
    }}
    .code-line {{
      display: grid;
      grid-template-columns: 52px minmax(0, 1fr);
      min-height: 26px;
    }}
    .code-line span {{
      padding: 3px 12px;
      color: #8fa29b;
      text-align: right;
      border-right: 1px solid rgba(255,255,255,.12);
      user-select: none;
    }}
    .code-line code {{ padding: 3px 14px; white-space: pre; }}
    .table-wrap {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      max-height: 560px;
    }}
    table {{
      width: 100%;
      min-width: 760px;
      border-collapse: collapse;
      font-size: .9rem;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 1;
      color: var(--muted);
      background: #f7f9fb;
      font-size: .74rem;
      text-transform: uppercase;
    }}
    td {{ font-family: Consolas, "Courier New", monospace; }}
    tr:last-child td {{ border-bottom: 0; }}
    .requirements td:last-child {{ background: var(--soft-blue); }}
    @media (max-width: 900px) {{
      .hero, .layout, .metrics {{ grid-template-columns: 1fr; }}
      .badge {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div>
        <div class="eyebrow">Compilador LangC#</div>
        <h1>Relatorio de Analise</h1>
        <p class="file">{html_escape(resultado.origem)}</p>
      </div>
      <div class="badge {status_classe}">{status_texto}</div>
    </div>
  </header>
  <main class="wrap">
    <section class="metrics">
      <div class="metric"><span>Fase</span><strong>{html_escape(resultado.fase)}</strong></div>
      <div class="metric"><span>Tokens</span><strong>{tokens_count}</strong></div>
      <div class="metric"><span>Passos sintaticos</span><strong>{len(resultado.passos_sintaticos)}</strong></div>
      <div class="metric"><span>Simbolos</span><strong>{len(resultado.simbolos)}</strong></div>
    </section>
    <section class="{diagnostico_classe}">
      <h2>Diagnostico</h2>
      <p>{html_escape(resultado.diagnostico)}</p>
    </section>
    <section class="layout">
      <div>
        <section class="panel">
          <h2>Codigo-fonte</h2>
          {html_codigo(resultado.codigo)}
        </section>
        <section class="panel">
          <h2>Tokens</h2>
          {html_tabela(["#", "Codigo", "Token", "Lexema", "Linha", "Coluna"], linhas_tokens(resultado.tokens))}
        </section>
      </div>
      <div>
        <section class="panel requirements">
          <h2>Requisitos dos PDFs</h2>
          {html_tabela(["Fonte", "Regra", "Implementacao"], REQUISITOS_PDF)}
        </section>
        <section class="panel">
          <h2>Tabela de simbolos</h2>
          {html_tabela(["#", "Nome", "Categoria", "Tipo", "Nivel", "Linha", "Escopo", "Parametros"], linhas_simbolos(resultado.simbolos))}
        </section>
        <section class="panel">
          <h2>Eventos semanticos</h2>
          {html_tabela(["#", "Etapa", "Detalhe", "Linha", "Status"], linhas_eventos(resultado.eventos_semanticos))}
        </section>
      </div>
    </section>
    <section class="panel">
      <h2>Execucao sintatica tabular</h2>
      {html_tabela(["Passo", "CodTok", "Token", "Lexema", "Linha", "Pilha", "Acao"], linhas_passos(resultado.passos_sintaticos))}
    </section>
  </main>
</body>
</html>
"""
    caminho.write_text(documento, encoding="utf-8")
    resultado.relatorio = caminho
    return caminho


def gerar_indice_html(resultados: list[ResultadoCompilacao]) -> Path:
    PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_RELATORIOS / "index.html"
    linhas = []
    for resultado in resultados:
        rel = resultado.relatorio.name if resultado.relatorio else ""
        status = "OK" if resultado.sucesso else "ERRO"
        link = f"<a href=\"{html_escape(rel)}\">{html_escape(resultado.origem)}</a>" if rel else html_escape(resultado.origem)
        linhas.append(
            [
                link,
                status,
                resultado.fase,
                resultado.diagnostico,
                str(len([t for t in resultado.tokens if t.tipo != TokenType.EOF])),
                str(len(resultado.simbolos)),
            ]
        )

    linhas_html = []
    for linha in linhas:
        linhas_html.append(
            "<tr>"
            f"<td>{linha[0]}</td>"
            + "".join(f"<td>{html_escape(valor)}</td>" for valor in linha[1:])
            + "</tr>"
        )

    documento = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Compilador LangC# - Relatorios</title>
  <style>
    body {{
      margin: 0;
      background: #f4f6f8;
      color: #18212a;
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    header {{
      background: #17242d;
      color: white;
      border-bottom: 5px solid #176b87;
    }}
    .wrap {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; }}
    .hero {{ padding: 34px 0 28px; }}
    h1 {{ margin: 0; font-size: clamp(2rem, 4vw, 3.5rem); letter-spacing: 0; }}
    main {{ padding: 24px 0 44px; }}
    .panel {{
      background: white;
      border: 1px solid #d8e0e7;
      border-radius: 8px;
      box-shadow: 0 14px 32px rgba(24, 33, 42, .08);
      overflow: auto;
    }}
    table {{ width: 100%; min-width: 760px; border-collapse: collapse; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid #d8e0e7; text-align: left; vertical-align: top; }}
    th {{ color: #62707f; background: #f7f9fb; font-size: .76rem; text-transform: uppercase; }}
    td {{ font-family: Consolas, "Courier New", monospace; }}
    a {{ color: #176b87; font-weight: 800; }}
  </style>
</head>
<body>
  <header><div class="wrap hero"><h1>Relatorios LangC#</h1></div></header>
  <main class="wrap">
    <section class="panel">
      <table>
        <thead>
          <tr><th>Arquivo</th><th>Status</th><th>Fase</th><th>Diagnostico</th><th>Tokens</th><th>Simbolos</th></tr>
        </thead>
        <tbody>{''.join(linhas_html)}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    caminho.write_text(documento, encoding="utf-8")
    return caminho


def compilar_arquivo(caminho: Path, gerar_json: bool = True, gerar_html: bool = True) -> ResultadoCompilacao:
    codigo = ler_arquivo(caminho)
    resultado = compilar_codigo(codigo, str(caminho))
    if gerar_json:
        exportar_tokens_json(resultado, caminho)
    if gerar_html:
        gerar_relatorio_html(resultado)
    return resultado


def exemplos_padrao() -> list[Path]:
    arquivos: list[Path] = []
    for pasta in (PASTA_LANGC, PASTA_SEMANTICO):
        if pasta.is_dir():
            arquivos.extend(sorted(pasta.glob("*.txt"), key=lambda p: p.name.lower()))
    return arquivos


def mostrar_tabela_tokens(tokens_codigos: list[int], lexemas: list[str], linhas: list[int], incluir_eof: bool = False) -> None:
    registros = []
    for codigo, lexema, linha in zip(tokens_codigos, lexemas, linhas):
        if not incluir_eof and codigo == TokenType.EOF.value:
            continue
        registros.append((codigo, TokenType(codigo).name, lexema, linha))

    if not registros:
        print("Nenhum token para exibir.")
        return

    larguras = [
        max(len("CODIGO"), max(len(str(r[0])) for r in registros)),
        max(len("TOKEN"), max(len(r[1]) for r in registros)),
        max(len("LEXEMA"), max(len(r[2]) for r in registros)),
    ]
    cabecalho = f"{'CODIGO':<{larguras[0]}} | {'TOKEN':<{larguras[1]}} | {'LEXEMA':<{larguras[2]}} | LINHA"
    print(cabecalho)
    print("-" * len(cabecalho))
    for codigo, token, lexema, linha in registros:
        print(f"{codigo:<{larguras[0]}} | {token:<{larguras[1]}} | {lexema:<{larguras[2]}} | {linha}")


def compilar(fonte: str, mostrar_tokens: bool = True):
    resultado = compilar_codigo(fonte)
    tokens_codigos = [token.tipo.value for token in resultado.tokens]
    lexemas = [token.valor for token in resultado.tokens]
    linhas = [token.linha for token in resultado.tokens]

    if mostrar_tokens and resultado.tokens:
        mostrar_tabela_tokens(tokens_codigos, lexemas, linhas)

    print(resultado.diagnostico)
    return tokens_codigos, lexemas, linhas, resultado.sucesso


def resolver_entrada(texto: str) -> tuple[str, str, Path | None]:
    caminho = Path(texto)
    if caminho.is_file():
        return ler_arquivo(caminho), str(caminho), caminho
    return texto, "entrada direta", None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compilador LangC# com analise lexica, sintatica, semantica e relatorio HTML."
    )
    parser.add_argument(
        "entradas",
        nargs="*",
        help="Arquivos .txt para compilar. Sem argumentos, compila os exemplos em examples/.",
    )
    parser.add_argument("--sem-html", action="store_true", help="Nao gera relatorios HTML.")
    parser.add_argument("--sem-json", action="store_true", help="Nao gera JSON de tokens.")
    parser.add_argument("--codigo", help="Compila uma string de codigo diretamente.")
    args = parser.parse_args()

    resultados: list[ResultadoCompilacao] = []
    usando_exemplos_padrao = False

    if args.codigo is not None:
        codigo, origem, caminho = resolver_entrada(args.codigo)
        resultado = compilar_codigo(codigo, origem)
        if not args.sem_json:
            exportar_tokens_json(resultado, caminho)
        if not args.sem_html:
            gerar_relatorio_html(resultado)
        resultados.append(resultado)
    else:
        usando_exemplos_padrao = not args.entradas
        entradas = [Path(e) for e in args.entradas] if args.entradas else exemplos_padrao()
        if not entradas:
            print("Nenhum arquivo .txt encontrado em examples/langc ou examples/semantico.")
            return 1

        for caminho in entradas:
            try:
                resultados.append(
                    compilar_arquivo(caminho, gerar_json=not args.sem_json, gerar_html=not args.sem_html)
                )
            except RuntimeError as erro:
                print(erro)
                return 1

    indice = None
    if not args.sem_html:
        indice = gerar_indice_html(resultados)

    for resultado in resultados:
        status = "OK" if resultado.sucesso else "ERRO"
        print(f"[{status}] {resultado.origem}")
        print(f"  {resultado.diagnostico}")
        if resultado.json_tokens:
            print(f"  JSON: {resultado.json_tokens.relative_to(RAIZ_PROJETO)}")
        if resultado.relatorio:
            print(f"  HTML: {resultado.relatorio.relative_to(RAIZ_PROJETO)}")

    if indice:
        print(f"\nIndice HTML: {indice.relative_to(RAIZ_PROJETO)}")

    if usando_exemplos_padrao:
        return 0

    return 0 if all(r.sucesso for r in resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
