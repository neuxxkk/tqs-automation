# tqs-automation

Ferramenta de automação para extração e classificação de ferros de armadura em projetos estruturais no **TQS**. A partir de um desenho DWG aberto no editor, o script identifica automaticamente todos os ferros inteligentes (`IPOFER`), classifica cada um pela posição em relação à borda da viga e gera uma planilha Excel formatada com o relatório completo.

---

## Sumário

- [Download rápido (usuário leigo)](#download-rápido-usuário-leigo)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Dependências](#dependências)
- [Instalação](#instalação)
- [Publicação do instalador (maintainer)](#publicação-do-instalador-maintainer)
- [Como usar](#como-usar)
- [Como funciona](#como-funciona)
- [Saída — Planilha Excel](#saída--planilha-excel)
- [Configurações](#configurações)
- [Licença](#licença)

---

## Download rápido (usuário leigo)

Use o instalador com 1 clique:

- **Baixar agora (Windows):** https://github.com/neuxxkk/tqs-automation/releases/latest/download/Scripts-Formula-Setup.exe

Após baixar:

1. Execute o `Scripts-Formula-Setup.exe`.
2. Clique em **Avançar** até concluir.
3. Abra o programa **Scripts Formula** no menu Iniciar ou atalho da área de trabalho.

> O instalador executa uma configuração inicial para preparar todas as funcionalidades.

---

## Funcionalidades

- **Integração nativa com o TQS** — acessível diretamente pelo menu do editor via botão EAG.
- **Leitura de DWG** — lê linhas, polilinhas e objetos inteligentes (`IPOFER`) do desenho.
- **Classificação geométrica de ferros** em três categorias:
  - 🔴 **BORDA** — ferros próximos ao perímetro da viga (dentro da tolerância configurável).
  - 🟡 **ALTERNADO** — ferros com fator de alternância ativo.
  - 🔵 **INTERNO** — ferros internos simples.
- **Cálculo automático de comprimento de faixa** por posição.
- **Relatório Excel colorido** com totais por categoria, compatível com Excel 2019 e superior.

---

## Pré-requisitos

- TQS instalado com suporte à execução de scripts Python
- Python 3.13 com `pip` e variável de ambiente configurados
- Acesso ao pacote `TQSPythonInterface` da instalação do TQS

---

## Dependências

| Pacote | Versão necessária | Obrigatório | Finalidade |
|---|---|---|---|
| **Python** | `3.13` | Sim | Ambiente de execução |
| **TQSPythonInterface** | `2.1.7` | Sim | Módulos `TQSDwg`, `TQSGeo`, `TQSEag`, `TQSJan` |
| **xlsxwriter** | `>= 3.0.0` | Sim | Geração da planilha Excel com total compatibilidade com Excel 2019+ |
| **Pillow** | `>= 10.0.0` | Não | Necessário apenas se as imagens `detS.png` / `detAL.png` forem utilizadas |

> **Por que `xlsxwriter` e não `openpyxl`?**
> O Excel 2019 exige o atributo `applyFill="1"` no XML interno do arquivo `.xlsx` para renderizar cores em células. O `openpyxl` não gera esse atributo, fazendo com que toda formatação de cor seja silenciosamente ignorada em versões antigas do Excel. O `xlsxwriter` segue o padrão OOXML corretamente e funciona em todas as versões.

---

## Instalação

### Instalação para usuário final (recomendada)

1. Baixe o instalador em **Download rápido (usuário leigo)**.
2. Execute o setup e finalize o assistente.
3. Abra o atalho **Scripts Formula**.

### Instalação manual (modo desenvolvedor)

1. **Clone ou baixe** este repositório.

2. Instale o Python 3.13 com `pip` e variável de ambiente:
   - Download: https://www.python.org/downloads/release/python-31312/
   - Durante a instalação, marque **"Add Python to PATH"** e **"Install pip"**.

3. Instale as dependências Python:

   ```bash
   pip install xlsxwriter
   pip install pillow                                                     
   pip install C:\TQSW\EXEC\PYTHON\TQSPythonInterface-2.1.7-py313-none-any.whl
   ```

4. Copie todo o conteúdo de `\arquivos` e a pasta `imgs` para `C:\TQSW\EXEC\Python` do seu projeto TQS.

---

## Publicação do instalador (maintainer)

Arquivos já preparados no projeto:

- Script do Inno Setup: `instalador/ScriptsFormula.iss`
- Pós-instalação automática: `instalador/instalar_completo.bat`
- Build local do instalador: `instalador/build_installer.ps1`
- Workflow de build/release: `.github/workflows/build-installer.yml`

Fluxo recomendado:

1. Crie uma Release no GitHub.
2. O workflow vai gerar `Scripts-Formula-Setup.exe`.
3. O arquivo será anexado automaticamente na Release publicada.
4. Divulgue o link de download direto no README e na documentação interna do time.

Para build local em Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\instalador\build_installer.ps1
```

---

## Como usar

### Via botão no TQS (EAG)

1. Abra o desenho DWG no editor do TQS.
2. No menu **Relatório Ferros**, clique em **Extrair Ferros e Gerar Relatório**.
3. Acompanhe as mensagens de progresso no painel de saída do TQS.
4. O arquivo Excel é salvo automaticamente na mesma pasta do DWG:

   ```
   <pasta do DWG>\Ferro Corrido - <nome do desenho>.xlsx
   ```

> **Atenção:** se o arquivo Excel já estiver aberto, o TQS exibirá uma mensagem de erro pedindo que você o feche antes de tentar novamente.

### Via linha de comando (standalone)

Para executar fora do TQS (desde que os módulos `TQS` estejam disponíveis no ambiente Python):

```bash
python extracao_tabela_ferro.py
```

---

## Como funciona

```
Fase 1 ──► Fase 2 ──► Fase 3 ──► Fase 4 ──► Fase 5
Inicializa  Contorno   Extrai     Classifica  Gera
  o DWG     da Viga    os Ferros  os Ferros   Relatório
```

| Fase | Nome | Descrição |
|------|------|-----------|
| **1** | Inicialização | Conecta ao DWG aberto no TQS e resolve o caminho de saída da planilha. |
| **2** | Contorno da viga | Extrai segmentos de linha e polilinha dos níveis `228` (viga) e `227` (pilar) para delimitar o perímetro analisado. |
| **3** | Extração dos ferros | Lê todos os objetos `IPOFER` do desenho, coletando posição, bitola, quantidade, comprimento e faixas de distribuição. |
| **4** | Classificação geométrica | Calcula a distância de cada ponto de inserção do ferro aos segmentos do contorno. Ferros dentro da `TOLERANCIA` são marcados como **BORDA**; os demais são separados em **ALTERNADO** ou **INTERNO** conforme o `alternatingMode`. |
| **5** | Geração do relatório | Cria a planilha Excel com linhas coloridas por tipo, linhas em branco entre posições distintas, totais por categoria e bloco auxiliar de imagens (opcional). |

---

## Saída — Planilha Excel

O arquivo gerado contém uma aba **"Ferros"** com as seguintes colunas:

| Coluna | Descrição |
|---|---|
| **Posição** | Identificador do ferro (ex.: `N1`, `N2`, …) |
| **Quantidade** | Número de ferros da faixa |
| **Espaçamento (cm)** | Espaçamento entre ferros na faixa |
| **Compr. Faixa (cm)** | Comprimento total da faixa (`Quantidade × Espaçamento`) |
| **Tipo** | `BORDA`, `ALTERNADO` ou `INTERNO` |

Ao final da tabela são exibidos os totais:

| Linha | Cor | Valor |
|---|---|---|
| Total Geral | 🟢 Verde | Soma de todas as faixas |
| Total Alternados | 🟡 Amarelo | Soma das faixas `ALTERNADO` |
| Total Simples | 🔵 Azul | Soma das faixas `INTERNO` |
| Total Borda | 🔴 Vermelho | Soma das faixas `BORDA` |

Se as imagens `imgs\detS.png` e `imgs\detAL.png` existirem na mesma pasta do script, elas são inseridas à direita da tabela com os valores calculados de **Total Simples + Borda/2** e **Total Alternados**.

---

## Configurações

As constantes de configuração ficam no início de `extracao_tabela_ferro.py`:

| Constante | Padrão | Descrição |
|---|---|---|
| `TOLERANCIA` | `10` | Distância máxima (em unidades do DWG) para considerar um ferro como BORDA |
| `NIVEL_VIGA` | `228` | Nível DWG dos segmentos de contorno da viga |
| `NIVEL_PILAR` | `227` | Nível DWG adicional incluído no mapeamento do contorno |

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

> © 2026 Vítor Neuenschwander
