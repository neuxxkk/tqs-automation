## v2.0.0 - Refatoracao UX, Atualizador e Novos Scripts

### Novidades

**Central de Scripts (`app.py`)**
- Nova interface principal com sidebar de navegacao escura
- Links da sidebar executam os scripts diretamente
- Area de conteudo com scroll
- Secao "Sobre" para cada ferramenta, explicando o que faz
- Botao **Atualizar sistema** no rodape da sidebar

**Atualizador automatico (`updater.py`)**
- Consulta a versao mais recente no GitHub sem uso do `git`
- Exibe versao instalada vs. disponivel
- Baixa o instalador com barra de progresso em MB
- Lanca o instalador automaticamente ao concluir

**Dimensionamento de Vigas (`detalhes_viga.py`)**
- Janela de acompanhamento com etapas, barra de progresso e log de atividade
- Instrucoes passo a passo exibidas antes de cada selecao de pasta
- Botao "Selecionar" explicito; caixas de dialogo so abrem apos confirmacao do usuario
- Contagem de pavimentos baseada nos arquivos RELGER encontrados

**Calculo de Beiral (`calc_beiral.py`)**
- Paleta de cores unificada com a identidade visual Formula Engenharia
- Tipografia atualizada: Barlow Condensed, DM Sans, JetBrains Mono

**Auditoria ARMPIL**
- Nova planilha de auditoria incluida no instalador
- Novo extrator para apoiar conferencia dos dados de armacao de pilares

### Instalacao

- Pos-instalador atualizado com interface grafica dedicada
- Deteccao de Python mais robusta, evitando usar automaticamente builds experimentais free-threading (`python3.13t.exe`)
- Instalacao de dependencias ajustada para evitar falhas de compilacao do `PyMuPDF`
- Instalador recompilado sem incluir caches Python (`__pycache__` e `.pyc`)

### Identidade Visual

- Paleta unificada em todos os modulos: verde `#5a8a4a`, cinza-900 `#1e1e1c`, cinza-100 `#f1efe8`
- Botoes desabilitados com texto legivel sobre fundo verde

### Infraestrutura

- Reestruturacao de pastas: `src/`, `assets/`, `launchers/`, `installer/`, `audit/`
- `version.txt` instalado em `{app}` para controle de versao pelo atualizador
- CI/CD via GitHub Actions: build automatico do instalador ao publicar release
