# Compiladores - LangC#

Projeto final com o compilador concentrado em um unico arquivo:

- `src/compilador.py`: analisador lexico, analisador sintatico LL(1), analisador semantico, exportacao JSON e geracao de relatorios HTML.
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

Compilar um arquivo especifico:

```bash
python src/compilador.py examples/semantico/6_erro_semantico_const.txt
```

Compilar uma string diretamente:

```bash
python src/compilador.py --codigo "const limite = 10; int main() { return limite; }"
```

Arquivos gerados:

```text
outputs/tokens/
outputs/reports/
outputs/reports/index.html
```

Abra `web/index.html` ou `outputs/reports/index.html` no navegador para visualizar os resultados em HTML.

## Regras atendidas

- Lexico conforme o manual: identificadores ASCII ate 64 caracteres, numeros inteiros/reais, palavras reservadas, operadores e comentarios `ç#` e `ç@ ... @ç`.
- Sintatico preditivo tabular LL(1), com pilha e producoes registradas no relatorio.
- Semantico conforme `AcoesSemantico.pdf`: tabela de simbolos com Nome, Categoria, Tipo e Nivel; `const` global como categoria `constante`; erro com linha quando uma constante recebe novo valor.
- Semantico adicional para o trabalho final: uso antes de declaracao, escopo, funcoes, parametros, chamadas e incompatibilidade entre `int` e `float`.

## Observacoes

- Nao ha dependencias externas obrigatorias.
- A execucao padrao nao usa prompt interativo.
- Os exemplos com erro proposital tambem geram relatorio HTML, para demonstrar as fases de erro.
