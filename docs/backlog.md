## Planilha ARMPIL

### Calculo Escada

## 1. Esqueleto inicial do software

### Objetivo
Um programa que padronize e automatize o processo de cálculo estrutural de escadas (Construção civil).

### Tarefas
- [x] Levantar onde a formatacao de linhas e aplicada hoje em `LoadArmpil`, `LoadSele`, `FormatInputRange` e `ApplySeleFormatting`.
- [x] Criar um helper unico para pintar blocos por pilar, recebendo:
  - `Worksheet`
  - linha inicial/final
  - coluna do pilar
  - intervalo de colunas a colorir
- [x] Aplicar o helper na aba `ARMPIL` apos `SortSheetRangeByPilarLance`.
- [x] Padronizar a aba `SELE` para usar o mesmo criterio visual da aba `ARMPIL`.
- [x] Garantir que a troca de cor aconteca apenas quando o nome do pilar mudar.
- [x] Preservar bordas, formulas e formatos numericos existentes ao reaplicar as cores.
- [x] Reaplicar a alternancia ao limpar e recarregar dados.

### Criterios de aceite
- [x] Linhas do mesmo pilar ficam com a mesma cor de fundo.
- [x] O pilar seguinte troca para outra cor e assim sucessivamente.
- [x] A ordenacao por `Pilar + Lance` continua correta.
- [x] O visual fica igual nas abas `ARMPIL` e `SELE`.

