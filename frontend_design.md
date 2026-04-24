# Frontend Design & Interaction — Sistema Fórmula Engenharia

---

## 1. Direção Estética

### Conceito

O sistema é uma ferramenta técnica usada por engenheiros e desenhistas ao longo do dia de trabalho. O design parte de um princípio **industrial-refinado**: denso de informação, mas sem parecer pesado. Sem arredondamentos excessivos, sem gradientes decorativos. A estética remete a plantas técnicas — precisão, hierarquia clara, espaço bem ocupado.

O que torna esse sistema memorável: a **sidebar escura como âncora visual permanente**, o **timer verde pulsante** sempre visível quando há trabalho em andamento, e a **árvore de estrutura** do painel admin que revela edifícios inteiros de forma progressiva.

### Tom geral

Profissional, direto, confiável. Nada piscando sem motivo. Animações existem para orientar — não para decorar.

---

## 2. Identidade Visual

### Logotipo

Usar o logo oficial da Fórmula Engenharia e Consultoria (arquivo `logo-formula.png`) no header da sidebar. Versão horizontal, sobre fundo escuro. Manter o espaço de respiro mínimo de `16px` em todos os lados.

### Paleta de Cores

```css
:root {
  /* Verdes — identidade da marca */
  --verde-principal:   #5a8a4a;   /* botões primários, timer ativo, links */
  --verde-hover:       #3b6d11;   /* hover de botões, estado ativo de nav */
  --verde-claro:       #eaf3de;   /* fundo de badges "Ok", alertas positivos */
  --verde-texto:       #27500a;   /* texto sobre fundo verde claro */

  /* Cinzas — estrutura e texto */
  --cinza-900:         #1e1e1c;   /* sidebar, header escuro */
  --cinza-800:         #2c2c2a;   /* textos primários, headings */
  --cinza-600:         #6b6b6b;   /* textos secundários, labels, metadados */
  --cinza-300:         #b4b2a9;   /* bordas, divisores */
  --cinza-100:         #f1efe8;   /* fundo geral das páginas */
  --cinza-50:          #f8f7f4;   /* fundo de cards, painéis internos */

  /* Branco */
  --branco:            #ffffff;

  /* Status semânticos */
  --status-fazendo-bg:   #e6f1fb;   /* azul claro */
  --status-fazendo-text: #185fa5;   /* azul escuro */
  --status-ok-bg:        #eaf3de;   /* verde claro */
  --status-ok-text:      #27500a;   /* verde escuro */
  --status-atend-bg:     #faeeda;   /* âmbar claro */
  --status-atend-text:   #854f0b;   /* âmbar escuro */
  --status-gerado-bg:    #f1efe8;   /* cinza claro */
  --status-gerado-text:  #5f5e5a;   /* cinza médio */
  --status-impresso-bg:  #d3d1c7;
  --status-impresso-text:#2c2c2a;
  --status-montada-bg:   #2c2c2a;   /* fundo escuro — etapa final */
  --status-montada-text: #f1efe8;

  /* Feedback */
  --erro:     #e24b4a;
  --aviso:    #ba7517;
  --sucesso:  #3b6d11;

  /* Timer */
  --timer-bg:     #5a8a4a;
  --timer-texto:  #ffffff;
  --timer-pulso:  rgba(90, 138, 74, 0.25);
}
```

---

## 3. Tipografia

### Famílias

```css
/* Headings e labels de interface */
font-family: 'Barlow Condensed', sans-serif;

/* Corpo de texto, tabelas, formulários */
font-family: 'DM Sans', sans-serif;

/* Timer, timestamps, IDs técnicos */
font-family: 'JetBrains Mono', monospace;
```

Importação via Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?
  family=Barlow+Condensed:wght@400;500;600;700&
  family=DM+Sans:wght@400;500&
  family=JetBrains+Mono:wght@400;500&
  display=swap" rel="stylesheet">
```
