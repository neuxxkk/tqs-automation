# tqs-automation

Ferramenta de automação para extração e classificação de ferros de armadura em projetos estruturais no **TQS**. A partir de um desenho DWG aberto no editor do TQS, o script identifica automaticamente todos os ferros inteligentes (IPOFER), classifica cada um pela sua posição em relação à borda da viga e gera uma planilha Excel formatada com o relatório completo.

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
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

| Dependência | Descrição |
|---|---|
| **TQS** | Software de projeto estrutural com suporte a scripts Python (módulos `TQSDwg`, `TQSGeo`, `TQSEag`, `TQSJan`) |
| **Python 3** | Interpretador Python (geralmente já embutido no TQS) |
| **TQSPython** | Pacotes para manipulação do TQS (Python) |
| **openpyxl** | Geração de planilhas Excel |

Instale a biblioteca `openpyxl` e TQSPython (whl na root do TQSW) caso ainda não esteja disponível:

```bash
pip install openpyxl
pip install C:\TQSW\EXEC\PYTHON\TQSPythonInterface-2.1.7-py313-none-any.whl
```

---

## Instalação

1. **Clone ou baixe** este repositório:

   ```bash
   git clone https://github.com/neuxxkk/tqs-automation.git
   ```

2. Copie os arquivos `extracao.py` e `EAG.PYMEN` para a pasta de scripts Python do seu projeto TQS.

3. No TQS, carregue o arquivo `EAG.PYMEN` para registrar o botão no menu.

---

## Como usar

### Via botão no TQS (EAG)

1. Abra o desenho DWG desejado no editor do TQS.
2. No menu **Relatório Ferros**, clique em **Extrair Ferros e Gerar Relatório**.
3. Aguarde a conclusão — as mensagens de progresso aparecerão no painel de saída do TQS.
4. O arquivo Excel será salvo automaticamente em:

   ```
   ~/OneDrive/Desktop/relatoriostqs/relatorio_ferros.xlsx
   ```

### Modo standalone (linha de comando)

Para rodar fora do TQS (desde que os módulos TQS estejam disponíveis no ambiente):

1. Defina o nome do arquivo DWG na constante `NOMEDWG` em `extracao.py`.
2. Execute:

   ```bash
   python extracao.py
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
| **2** | Contorno da Viga | Extrai todos os segmentos de linha e polilinha com cores de borda (branca `7` e vermelha `1`) que delimitam a seção da viga. |
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

As principais constantes estão no início de `extracao.py`:

| Constante | Padrão | Descrição |
|---|---|---|
| `TOLERANCIA` | `0.5` | Tolerância geométrica em cm para comparação de cobrimento |
| `CORES_BORDA_VIGA` | `{7, 1}` | Cores DWG das linhas de borda (branca e vermelha) |
| `ARQUIVO_EXCEL` | `~/OneDrive/Desktop/relatoriostqs/relatorio_ferros.xlsx` | Caminho de saída da planilha |
| `NOMEDWG` | `"desenho.DWG"` | Nome do arquivo DWG (modo standalone) |

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

> © 2026 Vítor Neuenschwander
