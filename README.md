# LangÇ# - Compilador com Análise Léxica e Sintática

<div align="center">

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

## 📋 Descrição

**LangÇ#** é um compilador educacional que implementa um analisador léxico e sintático para uma linguagem de programação simplificada. O projeto foi desenvolvido para demonstrar os princípios fundamentais de compilação, tokenização e análise sintática usando a **análise preditiva recursiva descendente**.

## 🎯 Objetivos

- ✅ Implementar um analisador léxico (`Lexer`) completo e robusto
- ✅ Desenvolver um analisador sintático (`Parser`) baseado em gramática LL(1)
- ✅ Tratamento abrangente de erros léxicos e sintáticos
- ✅ Suporte para estruturas de controle (if/else, while)
- ✅ Validação de tipos e declarações

## 📚 Especificação da Linguagem

### Construtos Supportados

#### Tipos
```c
int     // inteiro
float   // número real
```

#### Palavras-chave Reservadas
```c
if      // condicional
else    // alternativa
while   // repetição
print   // saída
return  // retorno
```

#### Operadores

**Aritméticos:**
- `+` Adição
- `-` Subtração
- `*` Multiplicação
- `/` Divisão

**Relacionais:**
- `==` Igual
- `!=` Não igual
- `<` Menor que
- `>` Maior que
- `<=` Menor ou igual
- `>=` Maior ou igual

**Atribuição:**
- `=` Atribuição simples

### Exemplo de Código

```c
int x;
x = 10;

while (x > 0) {
    print x;
    x = x - 1;
}

if (x == 0) {
    print 42;
} else {
    print 0;
}
```

## 🏗️ Arquitetura

### Componentes Principais

```
compilador.py
├── TokenType (Enum)          # Definição de tipos de tokens
├── Token (Classe)            # Estrutura de um token
├── Lexer (Classe)            # Análise léxica
├── Parser (Classe)           # Análise sintática
└── Exceções Customizadas     # ErroLexico, ErroSintatico
```

### Fluxo de Processamento

```
Código-Fonte
     ↓
  [LEXER] → Tokenização
     ↓
  Lista de Tokens
     ↓
  [PARSER] → Análise Sintática
     ↓
  Árvore Sintática / Validação
```

## 🚀 Como Usar

### Pré-requisitos

- Python 3.8 ou superior

### Instalação

```bash
# Clone ou baixe o projeto
cd Compiladores

# Nenhuma dependência externa necessária!
```

### Execução

```bash
# Executar o compilador
python compilador.py

# ou usando o debugger
python -m pdb compilador.py
```

### Exemplo Prático

```python
from compilador import Lexer, Parser

# Código-fonte
codigo = """
int idade;
idade = 25;
if (idade >= 18) {
    print idade;
}
"""

# Análise léxica
lexer = Lexer(codigo)
tokens = lexer.tokenizar()

# Análise sintática
parser = Parser(tokens)
parser.parse()

print("✓ Código compilado com sucesso!")
```

## 📖 Detalhes Técnicos

### Análise Léxica

O `Lexer` realiza a tokenização do código-fonte identificando:

- **Palavras-chave** (if, else, while, int, float, print, return)
- **Identificadores** (nomes de variáveis e funções)
- **Literais numéricos** (inteiros e reais)
- **Operadores** (aritméticos, relacionais, atribuição)
- **Delimitadores** (parênteses, chaves, semicolon, vírgula)

**Regras léxicas implementadas:**
- Identificadores: `[a-zA-Z_][a-zA-Z0-9_]*`
- Inteiros: `[0-9]+`
- Reais: `[0-9]+\.[0-9]+`
- Comentários: Linhas em branco ignoradas

### Análise Sintática

O `Parser` implementa análise preditiva recursiva descendente que valida a estrutura do código conforme a gramática LL(1) definida.

**Método de análise:**
- Análise preditiva recursiva descendente
- Funções recursivas para cada regra gramatical
- Tratamento de produções unitárias e epsilon (ε)

## ⚠️ Tratamento de Erros

O compilador fornece mensagens de erro detalhadas:

```
ErroLexico: 
  └─ Caracteres inválidos
  └─ Tokens não reconhecidos

ErroSintatico:
  └─ Tokens fora de ordem
  └─ Valores faltantes obrigatórios
  └─ Estruturas malformadas
```

Cada erro inclui o número da linha para facilitar a depuração.

## 🧪 Testes

### Casos de Teste

```python
# Teste 1: Declaração válida
teste1 = "int x; x = 5;"

# Teste 2: Estrutura condicional
teste2 = """
if (x > 0) {
    print x;
}
"""

# Teste 3: Loop
teste3 = """
while (n > 0) {
    n = n - 1;
}
"""
```

Para adicionar mais testes, execute manualmente e verifique as saídas.

## 📁 Estrutura de Arquivos

```
Compiladores/
├── compilador.py          # Implementação principal
├── manual_langç.pdf       # Especificação completa da linguagem
└── README.md              # Este arquivo
```

## 🔧 Extensões Futuras

- [ ] Análise semântica
- [ ] Geração de código intermediário
- [ ] Otimizações de código
- [ ] Suporte a funções definidas pelo usuário
- [ ] Tabela de símbolos completa
- [ ] Sistema de tipos robusto
- [ ] Depurador integrado

## 📝 Documentação da Gramática

A gramática completa da linguagem LangÇ# é especificada em `manual_langç.pdf`. 

Estrutura gramatical resumida:

```
<Program> ::= <DeclList>
<DeclList> ::= <Decl> | <Decl> <DeclList>
<Decl> ::= <Type> <IdList> ;
<Type> ::= int | float
<IdList> ::= <Id> | <Id> , <IdList>
```

## 🐛 Debug e Troubleshooting

### Erro Comum: "Token Inesperado"
- Verifique se há espaçamento correto
- Confirme que delimitadores estão balanceados

### Erro: "Identificador Inválido"
- Certifique-se que nomes começam com letra ou `_`
- Evite palavras-chave reservadas

## 👨‍💻 Autor

Desenvolvido como projeto educacional de Compiladores.

## 📄 Licença

Este projeto é fornecido como material educacional.

---

<div align="center">

**Feito com ❤️ para aprendizado de Compiladores**

</div>
