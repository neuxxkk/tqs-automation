# Scripts Formula

Suite interna de automações da Fórmula Engenharia para apoiar fluxos de projeto, conferência e cálculo estrutural.

O sistema centraliza, em uma única interface, rotinas desktop e web para:

- `Dimensionar Vigas` no TQS e coletar relatórios `RELGER.LST`;
- `Grelha Não Linear` no TQS (formas + pré-processamento + análise + exportação);
- `Cálculo de Beiral` (Streamlit) com memorial técnico em PDF;
- `Cálculo de Escadas` (Streamlit) com preview, carregamentos e memória em Markdown/PDF;
- `Auditoria ARMPIL` via Excel com macros e integração com extrator Python.

## Visão funcional do sistema

### 1) Central desktop (`src/app.py`)

Ponto de entrada para o usuário final (atalho `launchers/Scripts Formula.bat`).

Responsável por:

- exibir o catálogo de ferramentas em interface Tkinter;
- abrir scripts Python locais de automação TQS;
- iniciar aplicações Streamlit de Beiral e Escadas em portas dedicadas;
- abrir a planilha de auditoria ARMPIL;
- verificar atualização automática e acionar o updater (`src/updater.py`).

### 2) Automações TQS

- `src/detalhes_viga.py`: executa processamento global de vigas no TQS e exporta `RELGER.LST` por pavimento para pasta escolhida.
- `src/extrair_dwg_grelha.py`: executa fluxo de grelha não linear no TQS com barra de progresso e logs.
- `src/install_tqs_files.py`: instala dependências Python e copia arquivos de integração para `C:\TQSW\EXEC\PYTHON`.

### 3) Aplicações web de cálculo

- `src/beiral/app.py` + `src/beiral/`: modelagem de beiral em balanço, combinação de cargas, cálculo de momento (incluindo majorador), visual técnico e PDF.
- `src/escada/app.py` + `src/escada/`: modelagem paramétrica de escadas (lances, vãos, apoios), preview geométrico, tabela de carregamentos e memorial Markdown/PDF.
- `src/ui/streamlit_theme.py`: identidade visual e componentes compartilhados entre apps Streamlit.

### 4) Auditoria ARMPIL

- `audit/auditoria_armpil_sele.xlsm`: planilha principal com macros de conferência.
- Módulos VBA em `audit/*.bas` e `audit/Planilha4.cls`.
- `src/armpil_extractor.py`: extrator de dados de armaduras em PDF (PyMuPDF + OCR) para apoio ao fluxo da auditoria.

### 5) Atualização e instalação

- `src/updater.py`: consulta releases no GitHub, detecta nova versão/pacote e dispara atualização.
- `installer/post_install_gui.pyw`: configuração inicial pós-instalação (pip + cópia para TQS).
- `installer/setup.iss`: empacotamento Inno Setup do instalador Windows.

## Estrutura do projeto

```text
assets/
  imgs/                     ícones e identidade visual
  tqs/                      arquivos copiados para integração no TQS

audit/
  auditoria_armpil_sele.xlsm
  *.bas / *.cls             macros e lógica VBA da auditoria

docs/
  backlog.md
  frontend_design.md
  escada/                   documentos de apoio

installer/
  setup.iss                 script Inno Setup
  post_install.bat
  post_install_gui.pyw      configurador pós-instalação
  build.ps1                 build local do instalador

launchers/
  Scripts Formula.bat       abre a central principal
  detalhes_viga.bat
  extrair_dwg_grelha_nao_linear.bat
  calc_beiral.bat
  calculo_escada.bat

src/
  app.py                    central desktop
  updater.py                atualização do sistema
  detalhes_viga.py          automação TQS de vigas
  extrair_dwg_grelha.py     automação TQS de grelha não linear
  armpil_extractor.py       extração ARMPIL PDF -> CSV
  install_tqs_files.py      instalação de dependências + cópia para TQS
  beiral/                   domínio e app web de beiral
  escada/                   domínio e app web de escadas
  ui/                       tema e componentes Streamlit

tests/
  escada/                   testes de domínio, cálculo, desenho e memória
  test_armpil_extractor.py  testes do extrator ARMPIL
```

## Fluxos de execução

### Fluxo padrão (usuário final)

1. Abrir `Scripts Formula` pelo atalho.
2. Escolher a automação desejada na central.
3. Executar o fluxo guiado da ferramenta.

### Execução direta por módulo (desenvolvimento)

```powershell
python .\src\app.py
python .\src\detalhes_viga.py
python .\src\extrair_dwg_grelha.py
python -m streamlit run .\src\beiral\app.py --server.port 8507
python -m streamlit run .\src\escada\app.py --server.port 8508
python .\src\armpil_extractor.py
```

## Instalação

### Usuário final

1. Execute `dist/Scripts-Formula-Setup.exe`.
2. Conclua o assistente.
3. Aguarde a configuração inicial.
4. Abra `Scripts Formula` pelo atalho criado.

### Ambiente de desenvolvimento (Windows + Python 3.13)

```powershell
python -m pip install --upgrade pip
python -m pip install xlsxwriter pillow streamlit==1.56.0 fpdf2 matplotlib PyMuPDF rapidocr_onnxruntime
```

Se precisar replicar a integração com TQS:

```powershell
python .\src\install_tqs_files.py
```

## Testes

A suíte automatizada atual cobre principalmente os módulos Python de `escada` e o extrator ARMPIL.

```powershell
python -m pytest
```

## Build do instalador

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build.ps1
```

## Observações de manutenção

- A central desktop, o updater e as automações TQS foram desenhados para ambiente Windows.
- As apps Streamlit de Beiral e Escadas compartilham padrão visual e componentes em `src/ui/`.
- A auditoria ARMPIL depende de macros habilitadas no Excel.
- O processamento TQS depende da instalação local do TQS e do módulo Python disponível no ambiente (`TQSBuild`, `TQSExec`).

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
