# Scripts Formula

Suite interna de automacoes da Formula Engenharia para apoio a fluxos de projeto, conferencia e calculo estrutural.

Hoje o sistema reune quatro frentes principais em uma central unica:

- `Dimensionar Vigas`: processamento de vigas no TQS e coleta dos `RELGER.LST`.
- `Calculo de Beiral`: aplicacao web em Streamlit para calculo estrutural e emissao de memorial.
- `Calculo de Escadas`: aplicacao web em Streamlit para modelagem de lances, carregamentos e memoria de calculo.
- `Auditoria ARMPIL`: planilha Excel com macros para conferencia de armacao de pilares.

## Estrutura do projeto

```text
assets/            arquivos visuais e scripts copiados para o TQS
audit/             planilha Excel, modulos VBA e apoio da auditoria ARMPIL
docs/              diretrizes visuais e backlog
installer/         setup Inno, pos-instalacao e build do instalador
launchers/         atalhos .bat para abrir a central e utilitarios
src/               app principal, utilitarios Python e modulos de dominio
tests/             testes automatizados dos modulos Python
```

## Experiencia principal

O ponto de entrada para usuarios finais e a central grafica em `src/app.py`, aberta pelo atalho `launchers/Scripts Formula.bat`.

Ela concentra:

- navegacao lateral com acesso rapido a cada ferramenta;
- abertura silenciosa das apps web em portas locais dedicadas;
- abertura orientada da auditoria ARMPIL;
- atualizacao do sistema via `src/updater.py`.

## Instalacao

### Usuario final

1. Execute o instalador gerado em `dist/Scripts-Formula-Setup.exe`.
2. Conclua o assistente.
3. Aguarde a configuracao inicial instalar as dependencias Python.
4. Abra `Scripts Formula` pelo atalho criado.

### Ambiente de desenvolvimento

1. Instale Python 3.13 no Windows.
2. Instale as dependencias principais:

```powershell
python -m pip install --upgrade pip
python -m pip install xlsxwriter pillow streamlit==1.56.0 fpdf2 matplotlib PyMuPDF
```

3. Se precisar copiar os arquivos de integracao para o TQS:

```powershell
python .\src\install_tqs_files.py
```

4. Para executar a central localmente:

```powershell
python .\src\app.py
```

## Aplicacoes web

### Calculo de Beiral

- script: `src/beiral/app.py`
- porta local padrao: `8507`
- modulo de dominio: `src/beiral/`

### Calculo de Escadas

- script: `src/escada/app.py`
- porta local padrao: `8508`
- modulo de dominio: `src/escada/`
- testes dedicados em `tests/escada/`

## Instalador

Arquivos principais:

- `installer/setup.iss`: empacotamento Windows com Inno Setup
- `installer/post_install_gui.pyw`: interface da configuracao inicial
- `installer/build.ps1`: build local do instalador

Build local:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\build.ps1
```

## Observacoes de manutencao

- `beiral/` e `escada/` seguem o mesmo padrao: `app.py` de entrada dentro do pacote e modulos de dominio ao lado.
- A auditoria ARMPIL depende de macros habilitadas no Excel.
- O modulo de escadas depende de `matplotlib` alem das dependencias comuns de Streamlit.

## Licenca

Distribuido sob a licenca MIT. Veja [LICENSE](LICENSE).
