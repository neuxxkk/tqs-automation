# tqs-automation

Ferramenta de automação para extração e classificação de ferros de armadura em projetos estruturais no **TQS**. A partir de um desenho DWG aberto no editor do TQS, o script identifica automaticamente todos os ferros inteligentes (IPOFER), classifica cada um pela sua posição em relação à borda da viga e gera uma planilha Excel formatada com o relatório completo.

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Dependências](#dependências)
- [Instalação](#instalação)
- [Como usar](#como-usar)
  - [Via botão no TQS (EAG)](#via-botão-no-tqs-eag)
  - [Modo standalone (linha de comando)](#modo-standalone-linha-de-comando)
- [Como funciona](#como-funciona)
- [Saída — Planilha Excel](#saída--planilha-excel)
- [Configurações](#configurações)
- [Licença](#licença)

---

## Funcionalidades

- **Integração com o TQS** — Acessível diretamente pelo menu do editor via botão EAG.
- **Leitura de DWG** — Lê linhas, polilinhas e objetos inteligentes (IPOFER) do desenho.
- **Classificação geométrica de ferros** em três categorias:
  - 🔴 **BORDA** — Ferros próximos ao perímetro da viga (dentro do cobrimento).
  - 🟡 **ALTERNADO** — Ferros distribuídos com fator de alternância.
  - 🔵 **INTERNO** — Ferros internos simples.
- **Cálculo de espaçamento** por faixa de distribuição.
- **Relatório Excel** formatado e colorido com totais por categoria.

---

## Pré-requisitos

- TQS instalado e com suporte à execução de scripts Python
- Python compatível com a interface do TQS
- Acesso ao pacote TQSPython da instalação do TQS

---

## Dependências

| Biblioteca / pacote | Versão | Obrigatória | Finalidade |
|---|---|---|---|
| **Python** | `3.13.12` | Sim | Ambiente Python identificado neste workspace |
| **TQSPythonInterface** | `2.1.7` | Sim | Disponibiliza o módulo `TQS` e os submódulos `TQSDwg`, `TQSGeo`, `TQSEag` e `TQSJan` |
| **openpyxl** | `>= 3.1.0` | Sim | Geração e formatação da planilha Excel |
| **Pillow** | `>= 10.0.0` | Sim | Suporte a imagens PNG inseridas na planilha via `openpyxl.drawing.image.Image` |

Bibliotecas importadas diretamente pelo script `extracao_tabela_ferro.py`:

- **Bibliotecas padrão do Python**: `math`, `os`
- **Bibliotecas do TQS / TQSPython**: `TQS.TQSDwg`, `TQS.TQSGeo`, `TQS.TQSEag`, `TQS.TQSJan`
- **Bibliotecas externas**: `openpyxl`, `Pillow`

---

## Instalação

1. **Clone ou baixe** este repositório.

3. Instale as dependências Python necessárias:
  3.1. `https://www.python.org/downloads/release/python-31312/` | Adicionar PIP e variavel de ambiente
  3.2
    ```bash
    pip install openpyxl
    pip install pillow
    pip install C:\TQSW\EXEC\PYTHON\TQSPythonInterface-2.1.7-py313-none-any.whl
    ```

3. Copie a pasta `\scripts` e o arquivo `EAG.PYMEN` para a pasta `C:\TQSW\EXEC\Python` do seu projeto TQS.

---

## Como usar

### Via botão no TQS (EAG)

1. Abra o desenho DWG desejado no editor do TQS.
2. No menu **Relatório Ferros**, clique em **Extrair Ferros e Gerar Relatório**.
3. Aguarde a conclusão — as mensagens de progresso aparecerão no painel de saída do TQS.
4. O arquivo Excel será salvo automaticamente em:

   ```
  <pasta do DWG>/Ferro Corrido - <nome do desenho>.xlsx
   ```

### Modo standalone (linha de comando)

Para rodar fora do TQS (desde que os módulos TQS estejam disponíveis no ambiente):

1. Garanta que o ambiente Python tenha acesso ao módulo `TQS` fornecido pelo TQSPython.
2. Execute:

   ```bash
  python extracao_tabela_ferro.py
   ```

---

## Como funciona

O script é dividido em **5 fases** sequenciais:

```
Fase 1 ──► Fase 2 ──► Fase 3 ──► Fase 4 ──► Fase 5
Inicializa  Contorno   Extrai     Classifica  Gera
  o DWG     da Viga    os Ferros  os Ferros   Relatório
```

| Fase | Nome | Descrição |
|------|------|-----------|
| **1** | Inicialização | Abre o arquivo DWG e configura a tolerância geométrica (padrão: 0,5 cm). |
| **2** | Contorno da Viga | Extrai todos os segmentos de linha e polilinha dos níveis `228` (viga) e `227` (pilar) para delimitar a seção analisada. |
| **3** | Extração dos Ferros | Lê todos os objetos `IPOFER` (ferros inteligentes) do desenho, extraindo posição, bitola, quantidade, comprimento, cobrimento e faixas de distribuição. |
| **4** | Classificação Geométrica | Calcula a distância de cada ponto de inserção do ferro aos segmentos de contorno. Ferros dentro do cobrimento + tolerância são marcados como **BORDA**; os demais são separados em **ALTERNADO** ou **INTERNO**. |
| **5** | Geração do Relatório | Cria uma planilha Excel organizada por posição, com cabeçalhos, linhas coloridas por tipo e linhas de totalização. |

---

## Saída — Planilha Excel

O arquivo gerado (`relatorio_ferros.xlsx`) contém uma aba **"Ferros"** com as colunas:

| Coluna | Descrição |
|---|---|
| Posição | Identificador do ferro (ex.: `N1`, `N2`, ...) |
| Quantidade | Número de ferros da posição |
| Espaçamento (cm) | Espaçamento calculado entre ferros na faixa |
| Compr. Faixa (cm) | Comprimento total da faixa de distribuição |
| Tipo | `BORDA`, `ALT(1/N)` ou `INTERNO` |

Ao final da planilha, são exibidos os totais de comprimento por categoria:

- 🟢 **Total Geral**
- 🟡 **Total Alternados**
- 🔵 **Total Simples**
- 🔴 **Total Borda**

---

## Configurações

As principais constantes estão no início de `extracao_tabela_ferro.py`:

| Constante | Padrão | Descrição |
|---|---|---|
| `TOLERANCIA` | `0.5` | Tolerância geométrica em cm para comparação de cobrimento |
| `NIVEL_VIGA` | `228` | Nível DWG considerado como contorno da viga |
| `NIVEL_PILAR` | `227` | Nível DWG adicional considerado no mapeamento do contorno |

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

> © 2026 Vítor Neuenschwander
