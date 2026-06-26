# Compiladores - LangC#

Projeto final com o compilador concentrado em um unico arquivo:

- `src/compilador.py`: analisador lexico, analisador sintatico LL(1) com acoes semanticas embutidas, analisador semantico dedicado, exportacao JSON e geracao de relatorios HTML.
- `docs/Relatorio_Semantico_E5.docx`: relatorio da etapa semantica (acoes semanticas, gramatica com acoes, estrutura da tabela de simbolos e lista de erros).
- `web/index.html`: painel HTML para abrir os relatorios gerados.
- `docs/`: PDFs e manual usados como referencia.
- `examples/`: entradas de teste da linguagem e da atividade semantica.
- `outputs/`: tokens JSON e relatorios HTML gerados.

## Estrutura

```text
Compiladores/
|-- README.md
|-- src/
|   `-- compilador.py
|-- web/
|   `-- index.html
|-- examples/
|   |-- langc/
|   |-- semantico/
|   `-- ll1/
|-- outputs/
|   |-- reports/
|   `-- tokens/
|-- docs/
|   |-- manuals/
|   `-- activities/
`-- archives/
```

## Como executar

Gerar relatorios para todos os exemplos:

```bash
python src/compilador.py
```

Ao finalizar, o compilador abre automaticamente o indice HTML no navegador:

```text
outputs/reports/index.html
```

Compilar um arquivo especifico:

```bash
python src/compilador.py examples/semantico/6_erro_semantico_tipo.txt
```

Compilar uma string diretamente:

```bash
python src/compilador.py --codigo "int main() { int x; x = 10; print(x); return x; }"
```

Arquivos gerados:

```text
outputs/tokens/
outputs/reports/
outputs/reports/index.html
```

Abra `web/index.html` ou `outputs/reports/index.html` no navegador para visualizar os resultados em HTML.

Para gerar HTML sem abrir o navegador:

```bash
python src/compilador.py --nao-abrir-html
```

Para manter a execucao aberta depois de abrir o HTML, como no F5 do VS Code:

```bash
python src/compilador.py --manter-aberto
```

Para abrir todos os relatorios individuais em abas:

```bash
python src/compilador.py --abrir-todos-html
```

## Regras atendidas

- Lexico conforme a gramatica e o manual: identificadores ASCII ate 64 caracteres, numeros inteiros/reais, palavras reservadas, operadores e comentarios `ç#` e `ç@ ... @ç`.
- Sintatico preditivo tabular LL(1), com pilha e producoes registradas no relatorio.
- Sintatico alinhado a gramatica do PDF: programa formado por lista de funcoes, blocos, declaracoes locais, atribuicao, `if/else`, `while`, `print`, `return`, expressoes e chamadas de funcao.
- Semantico conforme a gramatica e o manual: tabela de simbolos com Nome, Categoria, Tipo e Nivel; uso antes de declaracao; escopos; funcoes; parametros; chamadas; `return`; e incompatibilidade entre `int` e `float`.
- Acoes semanticas junto ao analisador sintatico: marcadores `@decl_funcao`, `@fim_funcao`, `@decl_parametro`, `@decl_variavel`, `@usa_lhs`, `@usa_id` e `@checa_atrib` inseridos na gramatica e executados pelo parser LL(1) durante o reconhecimento (atende ao requisito de pelo menos 3 regras integradas ao parser).
- Tabela de simbolos exibida a cada modificacao: cada insercao gera um snapshot mostrado no relatorio HTML na secao "Tabela de simbolos a cada modificacao".

## Observacoes

- Nao ha dependencias externas obrigatorias.
- A execucao padrao nao usa prompt interativo.
- Os exemplos com erro proposital tambem geram relatorio HTML, para demonstrar as fases de erro.
