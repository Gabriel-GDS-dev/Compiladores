"""
Atividade de Compiladores - Analise Semantica

Resolucao baseada em:
docs/activities/AcoesSemantico.pdf

O PDF pede uma tabela de simbolos com Nome, Categoria, Tipo e Nivel, a insercao
de declaracoes const no nivel global e a regra principal da atividade:
o valor de uma constante nao pode ser alterado depois da declaracao.
"""

import argparse
import html
import io
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path

from compilador import (
    ErroLexico,
    ErroSintatico,
    Lexer,
    Parser,
    Token,
    TokenType,
    vetores_para_tokens,
)


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
EXEMPLO_PADRAO = RAIZ_PROJETO / "examples" / "semantico" / "6_erro_semantico_const.txt"
PASTA_RELATORIOS = RAIZ_PROJETO / "outputs" / "reports"


class ErroSemantico(Exception):
    pass


@dataclass
class Simbolo:
    nome: str
    categoria: str
    tipo: TokenType
    nivel: int
    linha: int
    origem: str


@dataclass
class AcaoPDF:
    passo: str
    trecho: str
    implementacao: str


@dataclass
class EventoSemantico:
    passo: int
    etapa: str
    detalhe: str
    linha: int | None = None
    status: str = "OK"


@dataclass
class ResultadoSemantico:
    origem: str
    codigo: str
    tokens: list[Token] = field(default_factory=list)
    simbolos: list[Simbolo] = field(default_factory=list)
    eventos: list[EventoSemantico] = field(default_factory=list)
    sucesso: bool = False
    diagnostico: str = ""
    saida_sintatica: str = ""
    relatorio: Path | None = None


ACOES_DO_PDF = [
    AcaoPDF(
        "1",
        "Usar uma estrutura para carregar a tabela de simbolos abaixo: Nome, Categoria, Tipo, Nivel.",
        "A classe Simbolo guarda exatamente esses campos e tambem a linha/origem para explicar o resultado.",
    ),
    AcaoPDF(
        "2",
        "Inserir na tabela de simbolos quando encontrar const.",
        "Quando aparece 'const nome = valor;', o nome fica em const + 1 e o valor em const + 3.",
    ),
    AcaoPDF(
        "3",
        "Nivel = 0 Global; Categoria = constante.",
        "Toda const declarada antes das funcoes entra como categoria constante e nivel 0.",
    ),
    AcaoPDF(
        "4",
        "Regra: valor nao pode ser alterado.",
        "Se um identificador constante aparecer seguido de '=', a regra semantica aponta erro.",
    ),
    AcaoPDF(
        "5",
        "Mostrar o numero da linha e o erro semantico.",
        "O diagnostico final sempre mostra a linha do token que violou a regra.",
    ),
]


def proximo_passo(eventos: list[EventoSemantico]) -> int:
    return len(eventos) + 1


def registrar(
    eventos: list[EventoSemantico],
    etapa: str,
    detalhe: str,
    linha: int | None = None,
    status: str = "OK",
):
    eventos.append(EventoSemantico(proximo_passo(eventos), etapa, detalhe, linha, status))


def mostrar_tabela(titulo: str, cabecalho: list[str], linhas: list[list[str]]):
    print(f"\n{titulo}")
    registros = [cabecalho] + linhas
    larguras = [
        max(len(str(linha[indice])) for linha in registros)
        for indice in range(len(cabecalho))
    ]

    for indice, linha in enumerate(registros):
        texto = " | ".join(
            str(valor).ljust(larguras[coluna])
            for coluna, valor in enumerate(linha)
        )
        print(texto)
        if indice == 0:
            print("-" * len(texto))


def mostrar_acoes_do_pdf():
    linhas = [
        [acao.passo, acao.trecho, acao.implementacao]
        for acao in ACOES_DO_PDF
    ]
    mostrar_tabela(
        "Passo a passo extraido de AcoesSemantico.pdf:",
        ["Passo", "O que o PDF pede", "Como o codigo executa"],
        linhas,
    )


def mostrar_codigo(origem: str, codigo: str):
    print(f"\nArquivo analisado: {origem}")
    print("\nCodigo-fonte:")
    for numero, linha in enumerate(codigo.splitlines(), start=1):
        print(f"{numero:>3} | {linha}")


def obter_codigo(entrada: str) -> tuple[str, str, Path | None]:
    caminho = Path(entrada)
    if caminho.is_file():
        return caminho.read_text(encoding="utf-8"), str(caminho), caminho
    return entrada, "entrada direta", None


def nome_tipo(tipo: TokenType) -> str:
    if tipo == TokenType.INT:
        return "int"
    if tipo == TokenType.FLOAT:
        return "float"
    return tipo.name.lower()


def papel_semantico(tokens: list[Token], indice: int) -> str:
    token = tokens[indice]

    if token.tipo == TokenType.ID and token.valor == "const":
        return "inicio da acao const do PDF"

    if (
        indice > 0
        and tokens[indice - 1].tipo == TokenType.ID
        and tokens[indice - 1].valor == "const"
        and token.tipo == TokenType.ID
    ):
        return "const + 1: nome inserido na tabela"

    if (
        indice > 0
        and tokens[indice - 1].tipo == TokenType.ASSIGN
        and token.tipo in (TokenType.NUM, TokenType.ID)
    ):
        return "const + 3 ou valor usado na atribuicao"

    if token.tipo == TokenType.ID and indice + 1 < len(tokens) and tokens[indice + 1].tipo == TokenType.ASSIGN:
        return "identificador antes de atribuicao; verificar tabela"

    if token.tipo == TokenType.ASSIGN:
        return "atribuicao; corresponde a regra de alteracao"

    return "-"


def linhas_tokens(tokens: list[Token]) -> list[list[str]]:
    linhas = []
    for indice, token in enumerate(tokens, start=1):
        if token.tipo == TokenType.EOF:
            continue

        papel = papel_semantico(tokens, indice - 1)
        token_nome = "CONST" if token.tipo == TokenType.ID and token.valor == "const" else token.tipo.name
        linhas.append(
            [
                str(indice),
                token_nome,
                str(token.valor),
                str(token.tipo.value),
                str(token.linha),
                papel,
            ]
        )
    return linhas


def mostrar_tokens_semanticos(tokens: list[Token]):
    mostrar_tabela(
        "Tokens com papel na analise semantica:",
        ["#", "Token", "Lexema", "Codigo", "Linha", "Papel semantico"],
        linhas_tokens(tokens),
    )


def mostrar_tabela_simbolos(simbolos: list[Simbolo]):
    linhas = [
        [
            str(indice),
            simbolo.nome,
            simbolo.categoria,
            nome_tipo(simbolo.tipo),
            str(simbolo.nivel),
            str(simbolo.linha),
            simbolo.origem,
        ]
        for indice, simbolo in enumerate(simbolos, start=1)
    ]

    if not linhas:
        print("\nTabela de simbolos vazia.")
        return

    mostrar_tabela(
        "Tabela de simbolos carregada:",
        ["#", "Nome", "Categoria", "Tipo", "Nivel", "Linha", "Origem"],
        linhas,
    )


def eh_declaracao_const(tokens: list[Token], posicao: int) -> bool:
    return (
        posicao + 3 < len(tokens)
        and tokens[posicao].tipo == TokenType.ID
        and tokens[posicao].valor == "const"
        and tokens[posicao + 1].tipo == TokenType.ID
        and tokens[posicao + 2].tipo == TokenType.ASSIGN
    )


def inferir_tipo_constante(tokens: list[Token], inicio: int, fim: int, tipos: dict[str, TokenType]) -> TokenType:
    for token in tokens[inicio:fim]:
        if token.tipo == TokenType.NUM and "." in str(token.valor):
            return TokenType.FLOAT

        if token.tipo == TokenType.ID and tipos.get(str(token.valor)) == TokenType.FLOAT:
            return TokenType.FLOAT

    return TokenType.INT


def coletar_constantes_globais(
    tokens: list[Token],
    eventos: list[EventoSemantico],
) -> tuple[list[Simbolo], dict[str, TokenType], int]:
    simbolos = []
    tipos = {}
    posicao = 0

    registrar(
        eventos,
        "Preparar tabela",
        "Criada a estrutura Nome, Categoria, Tipo e Nivel solicitada no PDF.",
    )

    while eh_declaracao_const(tokens, posicao):
        token_const = tokens[posicao]
        token_nome = tokens[posicao + 1]
        pos_expr = posicao + 3
        fim_expr = pos_expr

        while fim_expr < len(tokens) and tokens[fim_expr].tipo != TokenType.SEMICOLON:
            fim_expr += 1

        if fim_expr >= len(tokens):
            raise ErroSintatico(
                f"Linha {token_const.linha}: faltou ';' ao final da declaracao const"
            )

        tipo = inferir_tipo_constante(tokens, pos_expr, fim_expr, tipos)
        nome = str(token_nome.valor)
        tipos[nome] = tipo

        registrar(
            eventos,
            "Encontrar const",
            f"Token 'const' encontrado; const + 1 aponta para o nome '{nome}'.",
            token_const.linha,
        )
        registrar(
            eventos,
            "Inferir tipo",
            f"const + 3 inicia o valor '{tokens[pos_expr].valor}', entao o tipo registrado e {nome_tipo(tipo)}.",
            tokens[pos_expr].linha,
        )

        simbolo = Simbolo(nome, "constante", tipo, 0, token_nome.linha, "declaracao const global")
        simbolos.append(simbolo)
        registrar(
            eventos,
            "Inserir simbolo",
            f"Inserido Nome={simbolo.nome}, Categoria=constante, Tipo={nome_tipo(tipo)}, Nivel=0.",
            token_nome.linha,
        )

        posicao = fim_expr + 1

    if not simbolos:
        registrar(
            eventos,
            "Declaracoes const",
            "Nenhuma declaracao const global foi encontrada antes do programa.",
        )

    return simbolos, tipos, posicao


def coletar_simbolos_do_programa(tokens: list[Token], simbolos: list[Simbolo], eventos: list[EventoSemantico]):
    posicao = 0

    while posicao < len(tokens):
        if (
            posicao + 2 < len(tokens)
            and tokens[posicao].tipo in (TokenType.INT, TokenType.FLOAT)
            and tokens[posicao + 1].tipo == TokenType.ID
            and tokens[posicao + 2].tipo == TokenType.LPAREN
        ):
            tipo_funcao = tokens[posicao].tipo
            nome_funcao = tokens[posicao + 1]
            simbolos.append(
                Simbolo(str(nome_funcao.valor), "funcao", tipo_funcao, 0, nome_funcao.linha, "cabecalho de funcao")
            )
            registrar(
                eventos,
                "Completar tabela",
                f"Funcao '{nome_funcao.valor}' inserida no nivel 0 para deixar a tabela completa.",
                nome_funcao.linha,
            )
            posicao += 3

            while posicao + 1 < len(tokens) and tokens[posicao].tipo != TokenType.RPAREN:
                if tokens[posicao].tipo in (TokenType.INT, TokenType.FLOAT) and tokens[posicao + 1].tipo == TokenType.ID:
                    simbolos.append(
                        Simbolo(
                            str(tokens[posicao + 1].valor),
                            "parametro",
                            tokens[posicao].tipo,
                            1,
                            tokens[posicao + 1].linha,
                            "parametro de funcao",
                        )
                    )
                    registrar(
                        eventos,
                        "Completar tabela",
                        f"Parametro '{tokens[posicao + 1].valor}' inserido no nivel 1.",
                        tokens[posicao + 1].linha,
                    )
                    posicao += 2
                    continue

                posicao += 1

        if (
            posicao + 2 < len(tokens)
            and tokens[posicao].tipo in (TokenType.INT, TokenType.FLOAT)
            and tokens[posicao + 1].tipo == TokenType.ID
            and tokens[posicao + 2].tipo == TokenType.SEMICOLON
        ):
            simbolos.append(
                Simbolo(
                    str(tokens[posicao + 1].valor),
                    "variavel",
                    tokens[posicao].tipo,
                    1,
                    tokens[posicao + 1].linha,
                    "declaracao local",
                )
            )
            registrar(
                eventos,
                "Completar tabela",
                f"Variavel local '{tokens[posicao + 1].valor}' inserida no nivel 1.",
                tokens[posicao + 1].linha,
            )
            posicao += 3
            continue

        posicao += 1


def verificar_alteracao_constante(
    tokens: list[Token],
    nomes_constantes: set[str],
    eventos: list[EventoSemantico],
):
    for indice, token in enumerate(tokens[:-1]):
        if token.tipo != TokenType.ID:
            continue

        if tokens[indice + 1].tipo != TokenType.ASSIGN:
            if str(token.valor) in nomes_constantes:
                registrar(
                    eventos,
                    "Consultar tabela",
                    f"Uso de '{token.valor}' encontrado; esta na tabela como constante, mas nao e atribuicao.",
                    token.linha,
                )
            continue

        if str(token.valor) not in nomes_constantes:
            registrar(
                eventos,
                "Consultar tabela",
                f"Atribuicao para '{token.valor}' permitida porque nao esta como categoria constante.",
                token.linha,
            )
            continue

        registrar(
            eventos,
            "Erro semantico",
            (
                f"'{token.valor}' esta na tabela como constante e aparece seguido de '='; "
                "isso viola a regra do PDF."
            ),
            token.linha,
            "ERRO",
        )
        raise ErroSemantico(
            f"Linha {token.linha}: o valor da constante '{token.valor}' nao pode ser alterado"
        )


def analisar_semantico(codigo: str, origem: str) -> ResultadoSemantico:
    resultado = ResultadoSemantico(origem=origem, codigo=codigo)

    lexer = Lexer(codigo)
    tokens_codigos, lexemas, linhas = lexer.tokenizar()
    tokens = vetores_para_tokens(tokens_codigos, lexemas, linhas)
    resultado.tokens = tokens
    registrar(
        resultado.eventos,
        "Analise lexica",
        f"{sum(1 for token in tokens if token.tipo != TokenType.EOF)} token(s) gerado(s).",
    )

    try:
        simbolos, tipos_constantes, posicao_programa = coletar_constantes_globais(tokens, resultado.eventos)
    except ErroSintatico as erro:
        resultado.diagnostico = str(erro)
        registrar(resultado.eventos, "Erro sintatico", str(erro), status="ERRO")
        return resultado

    resultado.simbolos = simbolos
    tokens_programa = tokens[posicao_programa:]

    parser = Parser(tokens_programa)
    buffer_sintatico = io.StringIO()
    try:
        with redirect_stdout(buffer_sintatico):
            parser.programa()
    except ErroSintatico as erro:
        resultado.saida_sintatica = buffer_sintatico.getvalue()
        resultado.diagnostico = str(erro)
        registrar(resultado.eventos, "Erro sintatico", str(erro), status="ERRO")
        return resultado

    resultado.saida_sintatica = buffer_sintatico.getvalue()
    registrar(
        resultado.eventos,
        "Analise sintatica",
        "Programa validado pelo analisador sintatico antes da checagem semantica.",
    )

    coletar_simbolos_do_programa(tokens_programa, resultado.simbolos, resultado.eventos)
    try:
        verificar_alteracao_constante(tokens_programa, set(tipos_constantes), resultado.eventos)
    except ErroSemantico as erro:
        resultado.diagnostico = str(erro)
        return resultado

    resultado.sucesso = True
    resultado.diagnostico = "Analise semantica concluida sem erros."
    registrar(
        resultado.eventos,
        "Resultado",
        resultado.diagnostico,
        status="OK",
    )
    return resultado


def html_escape(valor) -> str:
    return html.escape(str(valor), quote=True)


def html_tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    head = "".join(f"<th>{html_escape(coluna)}</th>" for coluna in cabecalho)
    body = []
    for linha in linhas:
        colunas = "".join(f"<td>{html_escape(valor)}</td>" for valor in linha)
        body.append(f"<tr>{colunas}</tr>")

    if not body:
        body.append(f"<tr><td colspan=\"{len(cabecalho)}\">Nenhum registro.</td></tr>")

    return (
        "<div class=\"table-wrap\"><table>"
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table></div>"
    )


def html_codigo(codigo: str) -> str:
    linhas = []
    for numero, linha in enumerate(codigo.splitlines(), start=1):
        linhas.append(
            "<div class=\"code-line\">"
            f"<span>{numero}</span><code>{html_escape(linha)}</code>"
            "</div>"
        )
    return f"<div class=\"code-box\">{''.join(linhas)}</div>"


def caminho_relatorio(origem: str, caminho_entrada: Path | None) -> Path:
    if caminho_entrada is not None:
        nome = f"{caminho_entrada.stem}_relatorio.html"
    else:
        nome = "entrada_direta_relatorio.html"

    return PASTA_RELATORIOS / nome


def gerar_relatorio_html(resultado: ResultadoSemantico, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    status_classe = "ok" if resultado.sucesso else "erro"
    status_texto = "Sem erro semantico" if resultado.sucesso else "Erro semantico"

    linhas_pdf = [
        [acao.passo, acao.trecho, acao.implementacao]
        for acao in ACOES_DO_PDF
    ]
    linhas_eventos = [
        [
            str(evento.passo),
            evento.etapa,
            evento.detalhe,
            "" if evento.linha is None else str(evento.linha),
            evento.status,
        ]
        for evento in resultado.eventos
    ]
    linhas_simbolos = [
        [
            str(indice),
            simbolo.nome,
            simbolo.categoria,
            nome_tipo(simbolo.tipo),
            str(simbolo.nivel),
            str(simbolo.linha),
            simbolo.origem,
        ]
        for indice, simbolo in enumerate(resultado.simbolos, start=1)
    ]

    documento = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Relatorio Semantico - {html_escape(resultado.origem)}</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --surface: #ffffff;
      --ink: #18212a;
      --muted: #64717f;
      --line: #d9e1e8;
      --accent: #176b87;
      --ok: #227252;
      --erro: #b23b32;
      --soft-ok: #e5f4ed;
      --soft-erro: #fde9e5;
      --soft-info: #e8f2f6;
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
      background: #18212a;
      color: #f8fbfc;
      border-bottom: 5px solid var(--accent);
    }}

    .wrap {{
      width: min(1160px, calc(100% - 32px));
      margin: 0 auto;
    }}

    .hero {{
      padding: 30px 0 28px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
    }}

    h1, h2, p {{ margin: 0; }}
    h1 {{ margin-top: 6px; font-size: clamp(2rem, 4vw, 3.4rem); line-height: 1; letter-spacing: 0; }}
    h2 {{ font-size: 1.16rem; }}
    main {{ padding: 24px 0 44px; }}

    .eyebrow {{
      color: #9bd3df;
      font-size: .78rem;
      font-weight: 800;
      text-transform: uppercase;
    }}

    .file {{ margin-top: 12px; color: #cbd9df; font-family: Consolas, "Courier New", monospace; overflow-wrap: anywhere; }}

    .badge {{
      min-width: 180px;
      padding: 14px 16px;
      border-radius: 8px;
      text-align: center;
      font-weight: 800;
      background: var(--soft-ok);
      color: var(--ok);
    }}

    .badge.erro {{ background: var(--soft-erro); color: var(--erro); }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}

    .metric, .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 16px 38px rgba(24, 33, 42, .08);
    }}

    .metric {{ padding: 16px; min-height: 88px; }}
    .metric span {{ display: block; color: var(--muted); font-size: .76rem; font-weight: 800; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 1.45rem; }}

    .panel {{ padding: 18px; margin-bottom: 18px; overflow: hidden; }}
    .panel.alert {{ border-color: #e9b1aa; background: var(--soft-erro); }}
    .panel.info {{ background: var(--soft-info); }}
    .panel h2 {{ margin-bottom: 12px; }}

    .layout {{
      display: grid;
      grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
      gap: 18px;
      align-items: start;
    }}

    .code-box {{
      background: #101820;
      color: #edf5f3;
      border-radius: 8px;
      overflow: auto;
      max-height: 560px;
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

    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }}
    table {{ width: 100%; min-width: 680px; border-collapse: collapse; background: var(--surface); }}
    th, td {{ padding: 10px 11px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); background: #f7f9fb; font-size: .76rem; text-transform: uppercase; }}
    td {{ font-family: Consolas, "Courier New", monospace; font-size: .9rem; }}
    tr:last-child td {{ border-bottom: 0; }}

    @media (max-width: 860px) {{
      .hero, .layout, .grid {{ grid-template-columns: 1fr; }}
      .badge {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div>
        <div class="eyebrow">AcoesSemantico.pdf</div>
        <h1>Analise Semantica</h1>
        <p class="file">{html_escape(resultado.origem)}</p>
      </div>
      <div class="badge {status_classe}">{status_texto}</div>
    </div>
  </header>
  <main class="wrap">
    <section class="grid">
      <div class="metric"><span>Tokens</span><strong>{len([t for t in resultado.tokens if t.tipo != TokenType.EOF])}</strong></div>
      <div class="metric"><span>Simbolos</span><strong>{len(resultado.simbolos)}</strong></div>
      <div class="metric"><span>Passos</span><strong>{len(resultado.eventos)}</strong></div>
      <div class="metric"><span>Regra</span><strong>const</strong></div>
    </section>
    <section class="panel {'info' if resultado.sucesso else 'alert'}">
      <h2>Diagnostico</h2>
      <p>{html_escape(resultado.diagnostico)}</p>
    </section>
    <section class="layout">
      <div>
        <section class="panel">
          <h2>Codigo analisado</h2>
          {html_codigo(resultado.codigo)}
        </section>
        <section class="panel">
          <h2>Tabela de simbolos</h2>
          {html_tabela(["#", "Nome", "Categoria", "Tipo", "Nivel", "Linha", "Origem"], linhas_simbolos)}
        </section>
      </div>
      <div>
        <section class="panel">
          <h2>Passos do PDF</h2>
          {html_tabela(["Passo", "Trecho do PDF", "Implementacao"], linhas_pdf)}
        </section>
        <section class="panel">
          <h2>Execucao passo a passo</h2>
          {html_tabela(["#", "Etapa", "Detalhe", "Linha", "Status"], linhas_eventos)}
        </section>
        <section class="panel">
          <h2>Tokens semanticamente relevantes</h2>
          {html_tabela(["#", "Token", "Lexema", "Codigo", "Linha", "Papel semantico"], linhas_tokens(resultado.tokens))}
        </section>
      </div>
    </section>
  </main>
</body>
</html>
"""
    caminho.write_text(documento, encoding="utf-8")
    resultado.relatorio = caminho
    return caminho


def executar(entrada: str, gerar_relatorio: bool = True) -> ResultadoSemantico:
    codigo, origem, caminho_entrada = obter_codigo(entrada)

    try:
        resultado = analisar_semantico(codigo, origem)
    except ErroLexico as erro:
        resultado = ResultadoSemantico(origem=origem, codigo=codigo)
        resultado.diagnostico = str(erro)
        registrar(resultado.eventos, "Erro lexico", str(erro), status="ERRO")

    if gerar_relatorio:
        gerar_relatorio_html(resultado, caminho_relatorio(origem, caminho_entrada))

    return resultado


def imprimir_resultado(resultado: ResultadoSemantico):
    mostrar_acoes_do_pdf()
    mostrar_codigo(resultado.origem, resultado.codigo)

    if resultado.tokens:
        mostrar_tokens_semanticos(resultado.tokens)

    mostrar_tabela_simbolos(resultado.simbolos)

    linhas_eventos = [
        [
            str(evento.passo),
            evento.etapa,
            evento.detalhe,
            "" if evento.linha is None else str(evento.linha),
            evento.status,
        ]
        for evento in resultado.eventos
    ]
    mostrar_tabela(
        "Execucao passo a passo:",
        ["#", "Etapa", "Detalhe", "Linha", "Status"],
        linhas_eventos,
    )

    print(f"\nDiagnostico final: {resultado.diagnostico}")
    if resultado.relatorio is not None:
        print(f"Relatorio HTML: {resultado.relatorio.relative_to(RAIZ_PROJETO)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analise semantica passo a passo conforme AcoesSemantico.pdf."
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        default=str(EXEMPLO_PADRAO),
        help="Caminho de um arquivo .txt ou codigo-fonte direto.",
    )
    parser.add_argument(
        "--sem-relatorio",
        action="store_true",
        help="Executa apenas no terminal, sem gerar HTML em outputs/reports.",
    )
    args = parser.parse_args()

    try:
        resultado = executar(args.entrada, gerar_relatorio=not args.sem_relatorio)
    except OSError as erro:
        print(f"Erro ao ler entrada: {erro}")
        return 1

    imprimir_resultado(resultado)
    return 0 if resultado.sucesso else 1


if __name__ == "__main__":
    main()
