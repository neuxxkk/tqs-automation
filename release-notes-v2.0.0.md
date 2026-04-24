## v2.0.0 — Refatoração UX, Atualizador e Novos Scripts

### Novidades

**Central de Scripts (`app.py`)**
- Nova interface principal com sidebar de navegação escura
- Links da sidebar executam os scripts diretamente
- Área de conteúdo com scroll
- Seção "Sobre" para cada ferramenta, explicando o que faz
- Botão **Atualizar sistema** no rodapé da sidebar

**Atualizador automático (`updater.py`)**
- Consulta a versão mais recente no GitHub sem uso do `git`
- Exibe versão instalada vs. disponível
- Baixa o instalador com barra de progresso em MB
- Lança o instalador automaticamente ao concluir

**Dimensionamento de Vigas (`detalhes_viga.py`)**
- Janela de acompanhamento com etapas, barra de progresso e log de atividade
- Instruções passo a passo exibidas antes de cada seleção de pasta
- Botão "Selecionar" explícito — caixas de diálogo só abrem após confirmação do usuário
- Contagem de pavimentos baseada nos arquivos RELGER encontrados

**Cálculo de Beiral (`calc_beiral.py`)**
- Paleta de cores unificada com a identidade visual Fórmula Engenharia
- Tipografia atualizada: Barlow Condensed, DM Sans, JetBrains Mono

### Identidade Visual
- Paleta unificada em todos os módulos: verde `#5a8a4a`, cinza-900 `#1e1e1c`, cinza-100 `#f1efe8`
- Botões desabilitados com texto legível sobre fundo verde

### Infraestrutura
- Reestruturação de pastas: `src/`, `assets/`, `launchers/`, `installer/`, `audit/`
- `version.txt` instalado em `{app}` para controle de versão pelo atualizador
- CI/CD via GitHub Actions: build automático do instalador ao publicar release
