# Compiler Construction — Subset C Compiler

![Language](https://img.shields.io/badge/Language-Python-blue)
![Source](https://img.shields.io/badge/Source-C%20Subset-pink)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![Developer](https://img.shields.io/badge/Developer-Leonard%20Simala-green)

---

## Table of Contents

- [Overview](#overview)
- [What is a Compiler?](#what-is-a-compiler)
- [Project Description](#project-description)
- [Project Structure](#project-structure)
- [Modules](#modules)
- [Pipeline](#pipeline)
- [Implementation Technique](#implementation-technique)
- [Tools & Technologies](#tools--technologies)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [References](#references)

---

## Overview

This project implements a **simple but functional compiler** for a subset of the C programming language, written entirely in Python.  
It was built incrementally over 3 months as part of a compiler construction course  
Over the years I have made incremental adjustments out of my love for Natural language processing ,  
covering all major phases of compilation from source scanning through to intermediate code generation.

> *"It is a simple compiler, but its sophistication lies in its simplicity."*

---

## What is a Compiler?

A compiler is a software tool that transforms source code written in a high-level programming language into machine code or an intermediate representation that can be executed by a computer.

A typical compiler is composed of the following phases:

| Phase | Module                          | Responsibility                                          |
|-------|---------------------------------|---------------------------------------------------------|
| 1     | **Lexical Analyser**            | Breaks source code into a stream of tokens              |
| 2     | **Syntax Analyser**             | Validates grammar and builds a parse tree               |
| 3     | **Semantic Analyser**           | Checks type correctness and semantic rules              |
| 4     | **Intermediate Code Generator** | Translates the parse tree into Three Address Code (TAC) |
| 5     | **Code Optimiser**              | Improves the intermediate code for efficient execution  |
| 6     | **Code Generator**              | Translates optimised code into machine code             |

> Some compilers include additional modules such as error reporting, debugging facilities, and symbol table management.

---

## Project Description

This repository implements a **subset C compiler** covering phases 1 through 4 of the compilation pipeline. The compiler accepts a small but well-defined grammar of the C language and processes it through each phase sequentially.

Each module is implemented as a **standalone, testable unit** that can be run independently or as part of the full pipeline.

---

## Project Structure

```
compiler-construction/
│
├── grammar/                    # BNF grammar accepted by the compiler
│
├── inputs/                     # Sample C source files for testing
│   ├── fibonacci.c
│   ├── marks.c
│   ├── hello.c
│   └── ...
│
├── outputs/                    # Generated compiler outputs
│   ├── tokens.txt
│   ├── parseTree.txt
│   ├── symbolTable.txt
│   ├── lexicalErrors.txt
│   ├── syntaxErrors.txt
│   └── threeAddressCodes.txt
│
├── errors/                     # Error logs
│
└── modules/                                # Core compiler modules
    ├── scanner/                            # Lexical analyser
    ├── parser/                             # Syntax analyser
    ├── parserTable/                        # LL(1) parsing table
    ├── symbolTableManager/                 # Symbol table management
    ├── dfa/                                # DFA-based token recognition
    ├── semanticAnalysis/                   # Semantic analyser
    ├── memory/                             # Memory manager
    └── intermediateCode/                   # Intermediate code generator (TAC)
```

---

## Modules

### 1. Scanner — Lexical Analyser (`modules/scanner/`)
- Reads a C source file character by character
- Uses a **Deterministic Finite Automaton (DFA)** to recognise tokens
- Classifies tokens into: `KEYWORD`, `ID`, `NUMBER`, `DECIMAL`, `LETTER`, `SYMBOL`, `ASSIGN`, `ADD`, `SUB`, `MULT`, `DIV`, `RELOP`, etc.
- Outputs a token stream to `outputs/tokens.txt`
- Reports lexical errors to `outputs/lexicalErrors.txt`

### 2. Parser — Syntax Analyser (`modules/parser/`)
- Accepts the token stream from the Scanner
- Implements a **predictive LL(1) top-down parser** driven by the parsing table
- Builds a **parse tree** using the `anytree` library
- Outputs the parse tree to `outputs/parseTree.txt`
- Reports syntax errors to `outputs/syntaxErrors.txt`

### 3. Semantic Analyser (`modules/semanticAnalysis/`)
- Walks the parse tree produced by the parser
- Checks for **type compatibility**, **undeclared variables**, **duplicate declarations**, and **function arity**
- Uses the symbol table to resolve identifiers across scopes

### 4. Intermediate Code Generator (`modules/intermediateCode/`)
- Traverses the validated parse tree
- Emits **Three Address Code (TAC)** instructions
- Uses **temporaries** (`t1`, `t2`, ...) for sub-expressions
- Uses **labels** (`L1`, `L2`, ...) for control flow (if/else, loops)
- Outputs TAC to `outputs/three_address_code.txt`

### Supporting Modules

| Module                | Purpose                                                                |
|-----------------------|------------------------------------------------------------------------|
| `symbolTableManager/` | Manages variable/function entries, scopes, and types across all phases |
| `dfa/`                | DFA definitions used by the scanner for token classification           |
| `parserTable/`        | LL(1) parsing table and production rules for the grammar               |
| `memory/`             | Allocates memory addresses to variables and temporaries                |

---

## Pipeline

```
C Source File
      │
      ▼
┌─────────────┐
│   Scanner   │ → tokens.txt, lexicalErrors.txt
└──────┬──────┘
       │  Token stream
       ▼
┌─────────────┐
│   Parser    │ → parseTree.txt, syntaxErrors.txt
└──────┬──────┘
       │  Parse tree
       ▼
┌──────────────────┐
│ Semantic Analyser│ → validates types & scopes
└──────┬───────────┘
       │  Validated parse tree
       ▼
┌─────────────────────┐
│  TAC Generator      │ → threeAddressCode.txt
└─────────────────────┘
```

---

## Implementation Technique

The compiler was built **incrementally**, with each module tested independently before integration:

- **Tokenisation** uses regular expressions combined into a single master pattern. The scanner loops over successive matches of this pattern against the source file.
- **DFA-based recognition** classifies each matched token through a Deterministic Finite Automaton defined in `dfa/`.
- **Parsing** uses a predictive LL(1) approach — no backtracking. The parser table maps `(non-terminal, lookahead)` pairs to production rules.
- **Parse tree construction** uses the `anytree` library, building the tree top-down as productions are applied.
- **TAC generation** walks the parse tree with a dispatcher pattern, mapping each grammar non-terminal to a dedicated handler method.

---

## Tools & Technologies

| Tool              | Purpose                               |
|-------------------|---------------------------------------|
| Python 3.13       | Primary implementation language       |
| `anytree`         | Parse tree construction and traversal |
| `re`              | Regular expressions for tokenisation  |
| VS Code / PyCharm | Development environment               |
| C language        | Source language for compiler input    |
| Drawing software  | Grammar and pipeline diagrams         |

---

## Getting Started

### Prerequisites

```bash
pip install anytree
```

### Clone the Repository

```bash
git clone https://github.com/Leonard-Simala/compiler-construction.git
cd compiler-construction
```

### Run the Compiler

```bash
# Run the full pipeline on a sample input
python modules/parser/parser.py
```

Output files will be generated in the `outputs/` directory.

---

## Usage

To compile a different C source file, change the `input_path` at the bottom of `parser.py`:

```python
if __name__ == "__main__":
    input_path = os.path.join(script_dir, "inputs/your_file.c")
    main(input_path)
```

Then run:

```bash
python modules/parser/parser.py
```

---

## References

1. Haralambous, Y. — *A Course in Natural Language Processing*
2. Geetha, T.V. — *Understanding Natural Language Processing*
3. Xavier, S.P.E. — *Theory of Automata, Formal Languages and Computation*
4. Cohen, D.I.A. — *Introduction to Computer Theory*
5. *Automata Theory* — Course Lecture Notes
6. *Compiler Construction* — Course Lecture Notes
7. Python `re` library documentation — https://docs.python.org/3/library/re.html
