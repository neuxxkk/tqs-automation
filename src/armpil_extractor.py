#!/usr/bin/env python3
"""
armpil_extractor.py  –  Extração ARMPIL PDF → CSV (sem IA)
==============================================================
Extrai armadura longitudinal de pranchas ARMPIL (TQS/Eberick/AltoQi)
por leitura posicional de texto vetorial no PDF.

Dependências:  pip install PyMuPDF
Uso:
    python armpil_extractor.py              → gera CSV
    python armpil_extractor.py --discover   → lista pilares e níveis encontrados
"""

import fitz          # PyMuPDF
import re, math, csv, sys, os, traceback, tempfile, unicodedata
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

PDF_PATH: Path | None = None
OUT_CSV: Path | None = None

# Mapeamento nível (m) → número do lance.
# Lance 0 (ou qualquer valor em LANCES_IGNORAR) é descartado do CSV.
# Execute com --discover para ver os níveis presentes no arquivo.
LANCE_MAP: dict[float, int] = {
    1040.25: 0,   # barras de espera – ignorar
    1043.40: 6,
    1046.60: 7,
}
LANCES_IGNORAR: set[int] = {0}

# Diâmetro mínimo para ser considerado armadura longitudinal (mm).
# Ø5 e Ø6,3 são estribos → excluir.
BITOLA_MIN_LONG = 8.0

# ══════════════════════════════════════════════════════════════════════════════
# REGEXES
# ══════════════════════════════════════════════════════════════════════════════
RE_NIVEL      = re.compile(r'^\+?(\d{3,4}[,.]\d{1,2})$')
RE_Px         = re.compile(r'^P(\d+[A-Z]?)$', re.I)
RE_QTY        = re.compile(r'^\d{1,3}$')
RE_PHI        = re.compile(r'^[ØO∅Φφ]\s*(\d+[,.]?\d*)$')
RE_C_SLASH    = re.compile(r'^C/')
RE_TITLE_PART = re.compile(r'P(\d+[A-Z]?)(?:\s*\([^)]*\))?', re.I)

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def norm(s: str) -> float:
    return float(s.replace(',', '.').strip())

def emit_result_line(line: str) -> None:
    result_file = os.environ.get("ARMPIL_RESULT_FILE", "").strip()
    if not result_file:
        return
    Path(result_file).write_text(f"{line}\n", encoding="utf-8")

def ascii_slug(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", ascii_text).strip("._")
    return safe or "armpil"

def resolve_output_csv(pdf_path: Path) -> Path:
    if not os.environ.get("ARMPIL_RESULT_FILE", "").strip():
        return pdf_path.with_name(f"{pdf_path.stem}_script.csv")

    configured_dir = os.environ.get("ARMPIL_OUTPUT_DIR", "").strip()
    if configured_dir:
        output_dir = Path(configured_dir)
    else:
        public_dir = os.environ.get("PUBLIC", "").strip()
        if public_dir:
            output_dir = Path(public_dir) / "Documents" / "Scripts Formula" / "ARMPIL"
        else:
            output_dir = Path(tempfile.gettempdir()) / "ScriptsFormula" / "ARMPIL"

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{ascii_slug(pdf_path.stem)}_script.csv"

def choose_paths(discover: bool) -> tuple[Path, Path | None]:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        pdf_name = filedialog.askopenfilename(
            title="Selecione o PDF ARMPIL",
            filetypes=[("PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not pdf_name:
            sys.exit("[CANCELADO] Nenhum PDF selecionado.")

        pdf_path = Path(pdf_name)
        out_csv = resolve_output_csv(pdf_path)
        if discover:
            return pdf_path, out_csv

        return pdf_path, out_csv
    finally:
        root.destroy()

def calc_as(qty: int, diam_mm: float) -> float:
    d_cm = diam_mm / 10.0
    return round(qty * math.pi * (d_cm / 2) ** 2, 2)

def parse_names(txt: str) -> list[str]:
    """'P5(T3)=P10(T3) (X2)' → ['P5', 'P10']"""
    return list(dict.fromkeys("P" + m.group(1).upper()
                               for m in RE_TITLE_PART.finditer(txt)))

def get_spans(page) -> list[dict]:
    spans = []
    raw = page.get_text("dict", flags=0)
    for b in raw["blocks"]:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            d = line.get("dir", (1, 0))
            angle = math.degrees(math.atan2(-d[1], d[0]))
            for sp in line["spans"]:
                t = sp["text"].strip()
                if not t:
                    continue
                bb = sp["bbox"]
                spans.append({
                    "t":   t,
                    "x0":  bb[0], "y0": bb[1],
                    "x1":  bb[2], "y1": bb[3],
                    "w":   bb[2] - bb[0],
                    "cx":  (bb[0] + bb[2]) / 2,
                    "cy":  (bb[1] + bb[3]) / 2,
                    "sz":  sp.get("size", 0),
                    "ang": angle,
                })
    return spans

def group_by_y(spans: list[dict], tol: float = 6) -> list[list[dict]]:
    if not spans:
        return []
    ss = sorted(spans, key=lambda s: s["cy"])
    rows, cur = [], [ss[0]]
    for sp in ss[1:]:
        if abs(sp["cy"] - cur[0]["cy"]) <= tol:
            cur.append(sp)
        else:
            rows.append(cur)
            cur = [sp]
    rows.append(cur)
    return rows

def closest_level_above(y_bar: float, levels: list[dict]):
    """
    Retorna o marcador de cota no TOPO do segmento em que a barra está
    (o topo do lance define o lance — em coords PDF, y menor = posição mais alta).
    Entre todos os candidatos (level.y < y_bar), pega o mais próximo (maior y).
    """
    candidates = [lv for lv in levels if lv["y"] < y_bar]
    if not candidates:
        return None
    return max(candidates, key=lambda lv: lv["y"])

def attach_box_bounds(boxes: list[dict], tol: float = 40) -> None:
    """Calcula limites horizontais de cada box a partir dos títulos vizinhos."""
    rows: list[list[dict]] = []

    for box in sorted(boxes, key=lambda b: b["cy"]):
        for row in rows:
            if abs(row[0]["cy"] - box["cy"]) <= tol:
                row.append(box)
                break
        else:
            rows.append([box])

    for row in rows:
        row.sort(key=lambda b: b["cx"])
        for i, box in enumerate(row):
            if i == 0:
                if len(row) == 1:
                    left = box["x0"] - max(120, box["w"])
                else:
                    left = box["cx"] - (row[i + 1]["cx"] - box["cx"]) / 2
            else:
                left = (row[i - 1]["cx"] + box["cx"]) / 2

            if i == len(row) - 1:
                if len(row) == 1:
                    right = box["x1"] + max(260, box["w"])
                else:
                    right = box["cx"] + (box["cx"] - row[i - 1]["cx"]) / 2
            else:
                right = (box["cx"] + row[i + 1]["cx"]) / 2

            box["x_left"] = left
            box["x_right"] = right

def horiz_overlap(a: dict, b: dict) -> float:
    return max(0.0, min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]))

def merge_title_candidates(candidates: list[dict]) -> list[dict]:
    """Une títulos quebrados em múltiplas linhas no mesmo box."""
    merged: list[dict] = []

    for cand in sorted(candidates, key=lambda c: (c["cy"], c["x0"])):
        target = None
        for box in merged:
            overlap = horiz_overlap(box, cand)
            if overlap <= 0:
                continue
            min_width = min(box["w"], cand["w"])
            if min_width <= 0:
                continue
            if overlap < 0.6 * min_width:
                continue
            gap = cand["y0"] - box["y1"]
            if gap < -5 or gap > 35:
                continue
            target = box
            break

        if target is None:
            merged.append({
                "parts": [cand],
                "x0": cand["x0"],
                "x1": cand["x1"],
                "y0": cand["y0"],
                "y1": cand["y1"],
                "w": cand["w"],
            })
            continue

        target["parts"].append(cand)
        target["x0"] = min(target["x0"], cand["x0"])
        target["x1"] = max(target["x1"], cand["x1"])
        target["y0"] = min(target["y0"], cand["y0"])
        target["y1"] = max(target["y1"], cand["y1"])
        target["w"] = target["x1"] - target["x0"]

    boxes: list[dict] = []
    for group in merged:
        parts = sorted(group["parts"], key=lambda p: (p["cy"], p["x0"]))
        raw = "".join(p["t"] for p in parts)
        names = parse_names(raw)
        if not names:
            continue
        boxes.append({
            "names": names,
            "raw": raw,
            "cx": sum(p["cx"] for p in parts) / len(parts),
            "cy": sum(p["cy"] for p in parts) / len(parts),
            "x0": group["x0"],
            "x1": group["x1"],
            "w": group["w"],
        })
    return boxes

# ══════════════════════════════════════════════════════════════════════════════
# IDENTIFICAÇÃO DE BOXES
# ══════════════════════════════════════════════════════════════════════════════

def find_boxes(spans: list[dict]) -> list[dict]:
    """Títulos de pilar: fonte sz≈15.5, horizontal."""
    candidates = []
    for sp in spans:
        if abs(sp["sz"] - 15.5) > 1.2:
            continue
        if abs(sp["ang"]) > 5:
            continue
        if not parse_names(sp["t"]):
            continue
        candidates.append(sp)
    boxes = merge_title_candidates(candidates)
    boxes = sorted(boxes, key=lambda b: (round(b["cy"] / 50) * 50, b["cx"]))
    attach_box_bounds(boxes)
    return boxes

def assign_levels(spans: list[dict], boxes: list[dict]) -> None:
    """Associa marcadores de nível a cada box."""
    level_spans = []
    for sp in spans:
        if abs(sp["sz"] - 11.7) > 0.8:
            continue
        if abs(sp["ang"]) > 5:
            continue
        m = RE_NIVEL.match(sp["t"])
        if not m:
            continue
        level_spans.append({"val": norm(m.group(1)), "x": sp["cx"], "y": sp["cy"]})

    for box in boxes:
        # Box cresce PARA BAIXO a partir do título (maior y = mais abaixo na página).
        # Limita y ao intervalo [título-50, título+650] para não misturar linhas de boxes.
        y_lo = box["cy"] - 50
        y_hi = box["cy"] + 650
        nearby = [
            lv for lv in level_spans
            if box["x_left"] <= lv["x"] <= box["x_right"]
            and y_lo <= lv["y"] <= y_hi
        ]
        # Deduplica por valor de nível (mesmo nível pode aparecer 2× por duplicação no PDF)
        seen: dict[float, dict] = {}
        for lv in sorted(nearby, key=lambda lv: (lv["val"], abs(lv["x"] - box["cx"]))):
            key = round(lv["val"], 2)
            if key not in seen:
                seen[key] = lv
        # Ordena por y DESCENDENTE (maior y = menor elevação = base do desenho)
        box["levels"] = sorted(seen.values(), key=lambda l: -l["y"])

# ══════════════════════════════════════════════════════════════════════════════
# EXTRAÇÃO DA LEGENDA HORIZONTAL
# ══════════════════════════════════════════════════════════════════════════════

def extract_long_bars(spans: list[dict], box: dict) -> list[tuple]:
    """
    Extrai barras longitudinais da legenda horizontal do box.
    Formato: Px  Qty  Ø Bitola   (sem C/ = não é estribo)
    Retorna: lista de (lance, qty, bitola)
    """
    if not box["levels"]:
        return []

    level_xs = [lv["x"] for lv in box["levels"]]
    x_min = min(box["x_left"], min(level_xs) - 80)
    x_max = box["x_right"]

    # Faixa y do box
    y_min = box["cy"] - 80            # acima do título
    y_max = max(lv["y"] for lv in box["levels"]) + 40

    # Filtra spans horizontais na área da legenda
    local = [
        sp for sp in spans
        if abs(sp["ang"]) < 8
        and x_min <= sp["cx"] <= x_max
        and y_min <= sp["cy"] <= y_max
    ]

    rows = group_by_y(local, tol=6)
    results = []

    for row in rows:
        row_x = sorted(row, key=lambda s: s["x0"])   # ordena por x

        # Descarta linha se tiver C/ (estribo)
        if any(RE_C_SLASH.match(s["t"]) for s in row_x):
            continue

        i = 0
        while i < len(row_x):
            if not RE_Px.match(row_x[i]["t"]):
                i += 1
                continue

            qty:  int | None   = None
            diam: float | None = None
            j = i + 1
            while j < len(row_x):
                if RE_Px.match(row_x[j]["t"]):
                    break
                if qty is None and RE_QTY.match(row_x[j]["t"]):
                    qty = int(row_x[j]["t"])
                elif qty is not None:
                    m = RE_PHI.match(row_x[j]["t"])
                    if m:
                        diam = norm(m.group(1))
                        break
                j += 1

            if qty is not None and diam is not None and diam >= BITOLA_MIN_LONG:
                bar_y = row_x[i]["cy"]
                lv    = closest_level_above(bar_y, box["levels"])
                if lv is not None:
                    lance = LANCE_MAP.get(round(lv["val"], 2), -1)
                    if lance >= 0 and lance not in LANCES_IGNORAR:
                        results.append((lance, qty, diam))

            i = j if j > i else i + 1

    return results

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    discover = "--discover" in sys.argv
    pdf_path, out_csv = choose_paths(discover)

    if not pdf_path.exists():
        sys.exit(f"[ERRO] Arquivo não encontrado:\n  {pdf_path}")

    print(f"Lendo: {pdf_path.name}")
    doc    = fitz.open(str(pdf_path))
    page   = doc[0]
    spans  = get_spans(page)
    boxes  = find_boxes(spans)
    assign_levels(spans, boxes)
    doc.close()

    print(f"Boxes identificados: {len(boxes)}")

    if discover:
        print("\n=== DISCOVER MODE ===")
        for b in boxes:
            lvs = [(f"+{lv['val']:.2f}", lv['y']) for lv in b["levels"]]
            print(f"\n  {b['raw']!r:40s}  ->  {b['names']}")
            print(f"    Niveis (val, y-PDF): {lvs}")
        print("\n=== LANCE_MAP atual ===")
        for val, lc in sorted(LANCE_MAP.items()):
            status = "(IGNORAR)" if lc in LANCES_IGNORAR else f"-> Lance {lc}"
            print(f"  +{val:.2f}  {status}")
        print("\nEdite LANCE_MAP no script e rode sem --discover para gerar o CSV.")
        return

    def fmt_num(val: float) -> str:
        if float(val).is_integer():
            return str(int(val))
        return f"{val:.2f}".rstrip("0").rstrip(".")

    # Coleta: (pilar, lance) → lista de (qty, diam)
    from collections import defaultdict
    raw_rows: dict[tuple, list] = defaultdict(list)
    for box in boxes:
        data = extract_long_bars(spans, box)
        for lance, qty, diam in data:
            for name in box["names"]:
                raw_rows[(name, lance)].append((qty, diam))

    # Agrega por (pilar, lance, bitola): bitolas distintas saem em linhas separadas
    all_rows: list[tuple] = []
    for (pilar, lance), entries in sorted(raw_rows.items()):
        # Deduplica entradas idênticas (PDF repete spans)
        entries = list(dict.fromkeys(entries))
        by_diam: dict[float, int] = defaultdict(int)
        for qty, diam in entries:
            by_diam[diam] += qty

        for diam in sorted(by_diam):
            qty = by_diam[diam]
            all_rows.append((pilar, lance, qty, fmt_num(diam), f"{calc_as(qty, diam):.2f}"))

    if out_csv is None:
        sys.exit("[ERRO] Caminho de saída do CSV não definido.")

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Pilar", "Lance", "Qtd(Qf)", "Bitola(mm)", "As Total (cm2)"])
        for row in all_rows:
            w.writerow(row)

    print(f"[OK] {len(all_rows)} registros -> {out_csv}")
    print(f"CSV_OUTPUT={out_csv}")
    emit_result_line(f"CSV_OUTPUT={out_csv}")

    # Preview
    if all_rows:
        print("\nPrimeiras 10 linhas:")
        print("Pilar;Lance;Qtd;Bitola;As")
        for r in all_rows[:10]:
            print(f"  {r[0]};{r[1]};{r[2]};{r[3]};{r[4]}")

if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        msg = str(exc)
        if msg:
            print(msg)
            emit_result_line(msg)
        raise
    except Exception:
        msg = traceback.format_exc()
        print(msg, file=sys.stderr)
        emit_result_line("[ERROPY] " + msg.strip())
        raise
