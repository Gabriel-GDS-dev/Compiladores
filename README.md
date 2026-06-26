# Compiladores - LangC#

Projeto final com o compilador concentrado em um unico arquivo:

- `src/compilador.py`: analisador lexico, analisador sintatico tabular com acoes semanticas embutidas, analisador semantico dedicado, exportacao JSON e geracao de relatorios HTML.
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

Executar os testes de regressao e conformidade:

```bash
python -m unittest discover -s tests -v
```

## Constantes globais

O requisito de `AcoesSemantico.pdf` usa a declaracao global abaixo, antes das funcoes:

```text
const LIMITE = 10;
const PI = 3.14;
```

O tipo e inferido pelo literal (`int` ou `float`). A constante entra na tabela de simbolos no nivel 0, categoria `constante`, e qualquer atribuicao posterior gera erro semantico com a linha.

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
- Sintatico preditivo tabular, com pilha e producoes registradas no relatorio. O conflito classico do `dangling else` e resolvido dando prioridade ao `else`, que fica associado ao `if` aberto mais proximo.
- Sintatico alinhado a gramatica do PDF: programa formado por lista de funcoes, blocos, declaracoes locais, atribuicao, `if/else`, `while`, `print`, `return`, expressoes e chamadas de funcao.
- Semantico conforme a gramatica e o manual: exige a funcao de entrada `main`; valida tabela de simbolos, uso antes de declaracao, escopos de blocos, sombreamento, funcoes, parametros, chamadas adiantadas, `return` e incompatibilidade entre `int` e `float`.
- Acoes semanticas junto ao analisador sintatico: marcadores de constante, funcao, bloco, parametro, variavel, uso e atribuicao sao executados pelo parser tabular durante o reconhecimento (atende ao requisito de pelo menos 3 regras integradas ao parser).
- Tabela de simbolos exibida a cada modificacao: insercoes e remocoes de escopo geram snapshots da tabela ativa na secao "Tabela de simbolos a cada modificacao".
- Constantes globais conforme `AcoesSemantico.pdf`: `const nome = num;`, categoria `constante`, nivel 0 e valor imutavel.

## Observacoes

- Nao ha dependencias externas obrigatorias.
- A execucao padrao nao usa prompt interativo.
- Os exemplos com erro proposital tambem geram relatorio HTML, para demonstrar as fases de erro.
