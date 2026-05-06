# Memória de cálculo - Sudoeste - Ed. Metallo

## Dados de entrada

- Escada da 1ª à 2ª laje
- fck = 35,000 MPa
- CP = 0,100 tF·m⁻²
- CA = 0,250 tF·m⁻²
- Número de lances = 3

## Geometria e apoios

| Lance | Apoios | bᵢ (m) | hᵢ (m) | Vãos |
|---:|---|---:|---:|---|
| 1 | laje + lance 3 | 1,370 | 0,120 | L₁,₁ = 0,550 m (escada) |
| 2 | pilar + viga | 1,215 | 0,120 | L₂,₁ = 1,255 m (patamar), L₂,₂ = 1,375 m (escada), L₂,₃ = 1,250 m (patamar) |
| 3 | laje + viga | 1,370 | 0,120 | L₃,₁ = 1,375 m (escada) |

## Fórmulas adotadas

- PPᵢ = 2,5 × hᵢ
- qᵢ,ⱼ = CP + CA + PPᵢ, para vãos tipo patamar
- qᵢ,ⱼ = CP + CA + PPᵢ + 0,300, para vãos tipo escada

## Carregamentos

| Lance | Vão | Tipo | L (m) | PPᵢ (tF·m⁻²) | qᵢ,ⱼ (tF·m⁻²) | Desenvolvimento | Observação |
|---:|---:|---|---:|---:|---:|---|---|

**Lance 1:** PP₁ = 2,5 × 0,120 = 0,300 tF·m⁻²
| 1 | 1 | escada | 0,550 | 0,300 | 0,950 | q₁,₁ = 0,100 + 0,250 + PP₁ + 0,300 = 0,950 | apoia em outro lance |

**Lance 2:** PP₂ = 2,5 × 0,120 = 0,300 tF·m⁻²
| 2 | 1 | patamar | 1,255 | 0,300 | 0,650 | q₂,₁ = 0,100 + 0,250 + PP₂ = 0,650 | - |
| 2 | 2 | escada | 1,375 | 0,300 | 0,950 | q₂,₂ = 0,100 + 0,250 + PP₂ + 0,300 = 0,950 | - |
| 2 | 3 | patamar | 1,250 | 0,300 | 0,650 | q₂,₃ = 0,100 + 0,250 + PP₂ = 0,650 | - |

**Lance 3:** PP₃ = 2,5 × 0,120 = 0,300 tF·m⁻²
| 3 | 1 | escada | 1,375 | 0,300 | 0,950 | q₃,₁ = 0,100 + 0,250 + PP₃ + 0,300 = 0,950 | - |
