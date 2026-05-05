#!/usr/bin/env python3
"""
armpil_extractor.py - Extracao ARMPIL PDF -> CSV

Extrai armadura longitudinal de pranchas ARMPIL (TQS/Eberick/AltoQi)
por leitura posicional de texto vetorial no PDF.

Dependencias: pip install PyMuPDF
Uso:
    python armpil_extractor.py
    python armpil_extractor.py --discover
"""

from __future__ import annotations

import csv
import math
import os
import re
import sys
import tempfile
import traceback
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


PDF_PATH: Path | None = None
OUT_CSV: Path | None = None
RESULT_FILE_INITIALIZED = False

ALLOWED_LONGITUDINAL_DIAMETERS = (10.0, 12.5, 16.0, 20.0, 25.0, 32.0)
BITOLA_MIN_LONG = 10.0
LOWEST_LEVEL_EXTRA_Y = 180.0
MIN_REBAR_SEGMENT_LENGTH = 60.0
REBAR_RIGHT_BORDER_TOL = 12.0
REBAR_DIVISION_X_PAD = 90.0
REBAR_ROW_TOL_Y = 10.0
ROTATED_LABEL_SEGMENT_TOL_X = 30.0
ROTATED_LABEL_SEGMENT_TOL_Y = 12.0
LEVEL_LINE_TOL_Y = 16.0
DIVISION_LINE_TOL_Y = 28.0
VERTICAL_LINE_TOL_X = 1.2
HORIZONTAL_LINE_TOL_Y = 1.2
SAME_LANCE_LEVEL_TOL = 1.0

# Historical defaults for recurring jobs. The user can confirm or override
# them in the level mapping dialog before the CSV is generated.
DEFAULT_LANCE_MAP: dict[float, int] = {
    1040.25: 0,
    1043.40: 6,
    1046.60: 7,
}

RE_NIVEL = re.compile(r"^\+?(\d{3,4}[,.]\d{1,2})$")
RE_PX = re.compile(r"^P(\d+[A-Z]?)$", re.I)
RE_QTY = re.compile(r"^\d{1,3}$")
RE_PHI = re.compile(r"^[O\u00D8\u2205\u03A6\u03C6]\s*(\d+[,.]?\d*)$", re.I)
RE_C_SLASH = re.compile(r"^C/")
RE_TITLE_PART = re.compile(r"((?:PAF|P)\d+[A-Z]?)(?:\s*\([^)]*\))?", re.I)
RE_PILAR_SORT = re.compile(r"^(PAF|P)(\d+)([A-Z]*)$", re.I)


def norm(text: str) -> float:
    return float(text.replace(",", ".").strip())


def emit_result_line(line: str) -> None:
    global RESULT_FILE_INITIALIZED

    result_file = os.environ.get("ARMPIL_RESULT_FILE", "").strip()
    if not result_file:
        return
    mode = "a" if RESULT_FILE_INITIALIZED else "w"
    with open(result_file, mode, encoding="utf-8") as file:
        file.write(f"{line}\n")
    RESULT_FILE_INITIALIZED = True


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
    env_pdf = os.environ.get("ARMPIL_PDF_PATH", "").strip()
    if env_pdf:
        pdf_path = Path(env_pdf)
        return pdf_path, resolve_output_csv(pdf_path)

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
        return pdf_path, out_csv
    finally:
        root.destroy()


def calc_as(qty: int, diam_mm: float) -> float:
    d_cm = diam_mm / 10.0
    return round(qty * math.pi * (d_cm / 2) ** 2, 2)


def fmt_num(val: float) -> str:
    if float(val).is_integer():
        return str(int(val))
    return f"{val:.2f}".rstrip("0").rstrip(".")


def format_level(level: float) -> str:
    return f"+{level:.2f}"


def format_level_list(levels: list[float]) -> str:
    return ",".join(f"{level:.2f}" for level in levels)


def parse_names(text: str) -> list[str]:
    names = [match.group(1).upper() for match in RE_TITLE_PART.finditer(text)]
    return list(dict.fromkeys(names))


def pillar_sort_key(name: str) -> tuple[int, int, str, str]:
    text = name.strip().upper()
    match = RE_PILAR_SORT.match(text)
    if not match:
        return (10**9, 10, text, text)

    prefix, number, suffix = match.groups()
    prefix_rank = 0 if prefix.upper() == "P" else 1
    return (int(number), prefix_rank, suffix or "", text)


def get_spans(page) -> list[dict]:
    spans: list[dict] = []
    raw = page.get_text("dict", flags=0)
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            direction = line.get("dir", (1, 0))
            angle = math.degrees(math.atan2(-direction[1], direction[0]))
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                x0, y0, x1, y1 = span["bbox"]
                spans.append(
                    {
                        "t": text,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "w": x1 - x0,
                        "cx": (x0 + x1) / 2,
                        "cy": (y0 + y1) / 2,
                        "sz": span.get("size", 0),
                        "ang": angle,
                    }
                )
    return spans


def get_drawing_lines(page) -> tuple[list[dict], list[dict]]:
    vertical: list[dict] = []
    horizontal: list[dict] = []
    seen_vertical: set[tuple[float, float, float]] = set()
    seen_horizontal: set[tuple[float, float, float, float]] = set()

    for drawing in page.get_drawings():
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue

            p1, p2 = item[1], item[2]
            x0, y0, x1, y1 = p1.x, p1.y, p2.x, p2.y

            if abs(x0 - x1) <= VERTICAL_LINE_TOL_X:
                top, bottom = sorted((y0, y1))
                length = bottom - top
                if length < MIN_REBAR_SEGMENT_LENGTH:
                    continue
                x = (x0 + x1) / 2
                key = (round(x, 1), round(top, 1), round(bottom, 1))
                if key in seen_vertical:
                    continue
                seen_vertical.add(key)
                vertical.append({"x": x, "y0": top, "y1": bottom, "length": length})
                continue

            if abs(y0 - y1) <= HORIZONTAL_LINE_TOL_Y:
                left, right = sorted((x0, x1))
                length = right - left
                if length <= 0:
                    continue
                y = (y0 + y1) / 2
                key = (round(left, 1), round(y, 1), round(right, 1), round(length, 1))
                if key in seen_horizontal:
                    continue
                seen_horizontal.add(key)
                horizontal.append({"x0": left, "x1": right, "y": y, "length": length})

    return vertical, horizontal


def group_by_y(spans: list[dict], tol: float = 6) -> list[list[dict]]:
    if not spans:
        return []

    ordered = sorted(spans, key=lambda span: span["cy"])
    rows: list[list[dict]] = []
    current = [ordered[0]]
    for span in ordered[1:]:
        if abs(span["cy"] - current[0]["cy"]) <= tol:
            current.append(span)
        else:
            rows.append(current)
            current = [span]
    rows.append(current)
    return rows


def attach_box_bounds(boxes: list[dict], tol: float = 40) -> None:
    rows: list[list[dict]] = []
    for box in sorted(boxes, key=lambda item: item["cy"]):
        for row in rows:
            if abs(row[0]["cy"] - box["cy"]) <= tol:
                row.append(box)
                break
        else:
            rows.append([box])

    for row in rows:
        row.sort(key=lambda item: item["cx"])
        for index, box in enumerate(row):
            if index == 0:
                if len(row) == 1:
                    left = box["x0"] - max(120, box["w"])
                else:
                    left = box["cx"] - (row[index + 1]["cx"] - box["cx"]) / 2
            else:
                left = (row[index - 1]["cx"] + box["cx"]) / 2

            if index == len(row) - 1:
                if len(row) == 1:
                    right = box["x1"] + max(260, box["w"])
                else:
                    right = box["cx"] + (box["cx"] - row[index - 1]["cx"]) / 2
            else:
                right = (box["cx"] + row[index + 1]["cx"]) / 2

            box["x_left"] = left
            box["x_right"] = right


def horiz_overlap(a: dict, b: dict) -> float:
    return max(0.0, min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]))


def merge_title_candidates(candidates: list[dict]) -> list[dict]:
    merged: list[dict] = []

    for candidate in sorted(candidates, key=lambda item: (item["cy"], item["x0"])):
        target = None
        for box in merged:
            overlap = horiz_overlap(box, candidate)
            if overlap <= 0:
                continue
            min_width = min(box["w"], candidate["w"])
            if min_width <= 0 or overlap < 0.6 * min_width:
                continue
            gap = candidate["y0"] - box["y1"]
            if gap < -5 or gap > 35:
                continue
            target = box
            break

        if target is None:
            merged.append(
                {
                    "parts": [candidate],
                    "x0": candidate["x0"],
                    "x1": candidate["x1"],
                    "y0": candidate["y0"],
                    "y1": candidate["y1"],
                    "w": candidate["w"],
                }
            )
            continue

        target["parts"].append(candidate)
        target["x0"] = min(target["x0"], candidate["x0"])
        target["x1"] = max(target["x1"], candidate["x1"])
        target["y0"] = min(target["y0"], candidate["y0"])
        target["y1"] = max(target["y1"], candidate["y1"])
        target["w"] = target["x1"] - target["x0"]

    boxes: list[dict] = []
    for group in merged:
        parts = sorted(group["parts"], key=lambda item: (item["cy"], item["x0"]))
        raw_text = "".join(part["t"] for part in parts)
        names = parse_names(raw_text)
        if not names:
            continue
        boxes.append(
            {
                "names": names,
                "raw": raw_text,
                "cx": sum(part["cx"] for part in parts) / len(parts),
                "cy": sum(part["cy"] for part in parts) / len(parts),
                "x0": group["x0"],
                "x1": group["x1"],
                "w": group["w"],
            }
        )
    return boxes


def find_boxes(spans: list[dict]) -> list[dict]:
    candidates = []
    for span in spans:
        if abs(span["sz"] - 15.5) > 1.2:
            continue
        if abs(span["ang"]) > 5:
            continue
        if not parse_names(span["t"]):
            continue
        candidates.append(span)

    boxes = merge_title_candidates(candidates)
    boxes.sort(key=lambda box: (round(box["cy"] / 50) * 50, box["cx"]))
    attach_box_bounds(boxes)
    return boxes


def assign_levels(spans: list[dict], boxes: list[dict]) -> None:
    level_spans = []
    for span in spans:
        if abs(span["sz"] - 11.7) > 0.8:
            continue
        if abs(span["ang"]) > 5:
            continue
        match = RE_NIVEL.match(span["t"])
        if not match:
            continue
        level_spans.append({"val": norm(match.group(1)), "x": span["cx"], "y": span["cy"]})

    for box in boxes:
        y_lo = box["cy"] - 50
        y_hi = box["cy"] + 650
        nearby = [
            level
            for level in level_spans
            if box["x_left"] <= level["x"] <= box["x_right"] and y_lo <= level["y"] <= y_hi
        ]

        if nearby:
            y_hi = max(y_hi, max(level["y"] for level in nearby) + LOWEST_LEVEL_EXTRA_Y + 80.0)
            nearby = [
                level
                for level in level_spans
                if box["x_left"] <= level["x"] <= box["x_right"] and y_lo <= level["y"] <= y_hi
            ]

        seen: dict[float, dict] = {}
        for level in sorted(nearby, key=lambda item: (item["val"], abs(item["x"] - box["cx"]))):
            key = round(level["val"], 2)
            if key not in seen:
                seen[key] = level

        box["levels"] = sorted(seen.values(), key=lambda item: item["y"], reverse=True)


def box_level_row_y(box: dict) -> float:
    level_ys = sorted((level["y"] for level in box.get("levels", [])), reverse=True)
    if not level_ys:
        return box["cy"]
    if len(level_ys) >= 2:
        return level_ys[1]
    return level_ys[0]


def refine_box_bounds_by_level_rows(boxes: list[dict], tol: float = 55) -> None:
    rows: list[list[dict]] = []

    for box in sorted(boxes, key=box_level_row_y):
        row_y = box_level_row_y(box)
        for row in rows:
            if abs(box_level_row_y(row[0]) - row_y) <= tol:
                row.append(box)
                break
        else:
            rows.append([box])

    for row in rows:
        if len(row) <= 1:
            continue

        row.sort(key=lambda item: item["cx"])
        for index, box in enumerate(row):
            if index == 0:
                left = box["cx"] - (row[index + 1]["cx"] - box["cx"]) / 2
            else:
                left = (row[index - 1]["cx"] + box["cx"]) / 2

            if index == len(row) - 1:
                right = box["cx"] + (box["cx"] - row[index - 1]["cx"]) / 2
            else:
                right = (box["cx"] + row[index + 1]["cx"]) / 2

            box["x_left"] = left
            box["x_right"] = right
            box.pop("_rebar_segments", None)


def horiz_overlap_len(left_a: float, right_a: float, left_b: float, right_b: float) -> float:
    return max(0.0, min(right_a, right_b) - max(left_a, left_b))


def attach_level_division_lines(boxes: list[dict], horizontal_lines: list[dict]) -> None:
    for box in boxes:
        if not box.get("levels"):
            continue

        box_width = max(1.0, box["x_right"] - box["x_left"])
        candidates: list[dict] = []
        for line in horizontal_lines:
            overlap = horiz_overlap_len(line["x0"], line["x1"], box["x_left"], box["x_right"])
            if overlap < max(80.0, box_width * 0.45):
                continue
            candidates.append(line)

        for level in box["levels"]:
            nearby = [
                line
                for line in candidates
                if abs(line["y"] - level["y"]) <= DIVISION_LINE_TOL_Y
            ]
            if nearby:
                best = max(
                    nearby,
                    key=lambda line: (
                        horiz_overlap_len(line["x0"], line["x1"], box["x_left"], box["x_right"]),
                        -abs(line["y"] - level["y"]),
                    ),
                )
                level["line_y"] = best["y"]
                box.setdefault("_division_lines", []).append(best)
            else:
                level["line_y"] = level["y"]


def collect_unique_levels(boxes: list[dict]) -> list[float]:
    values = {round(level["val"], 2) for box in boxes for level in box.get("levels", [])}
    return sorted(values)


def collect_assignable_levels(boxes: list[dict], spans: list[dict], vertical_lines: list[dict] | None = None) -> list[float]:
    levels = collect_unique_levels(boxes)
    probe_map = {level: index for index, level in enumerate(levels, start=1)}
    level_by_probe = {index: level for level, index in probe_map.items()}

    values: set[float] = set()
    for box in boxes:
        for lance, _qty, _diam, _source, _confirmed in extract_long_bars(spans, box, probe_map, vertical_lines):
            if lance in level_by_probe:
                values.add(level_by_probe[lance])

    return sorted(values)


def parse_env_lance_map() -> dict[float, int]:
    raw = os.environ.get("ARMPIL_LANCE_MAP", "").strip()
    if not raw:
        return {}

    mapping: dict[float, int] = {}
    for chunk in re.split(r"[;\n]+", raw):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        level_text, lance_text = chunk.split("=", 1)
        try:
            mapping[round(norm(level_text), 2)] = int(lance_text.strip())
        except ValueError:
            continue
    return mapping


def read_known_lances_from_env() -> list[int]:
    raw = os.environ.get("ARMPIL_KNOWN_LANCES", "").strip()
    if not raw:
        return []

    values: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            values.append(int(token))
        except ValueError:
            continue
    return sorted(dict.fromkeys(values))


def align_known_lances_to_levels(known_lances: list[int], level_count: int) -> list[int]:
    if level_count <= 0 or not known_lances:
        return []
    if len(known_lances) <= level_count:
        return known_lances
    return known_lances[-level_count:]


def build_default_lance_map(levels: list[float]) -> dict[float, int]:
    env_map = parse_env_lance_map()
    if env_map:
        return {level: env_map[level] for level in levels if level in env_map}

    ordered_levels = sorted(levels)
    known_lances = read_known_lances_from_env()
    aligned_lances = align_known_lances_to_levels(known_lances, len(ordered_levels))
    if aligned_lances:
        mapping = {level: lance for level, lance in zip(ordered_levels, aligned_lances)}
        if len(aligned_lances) == len(ordered_levels):
            return mapping

        last_level = ordered_levels[len(aligned_lances) - 1]
        trailing_levels = ordered_levels[len(aligned_lances) :]
        if trailing_levels and all(level - last_level <= SAME_LANCE_LEVEL_TOL for level in trailing_levels):
            for level in trailing_levels:
                mapping[level] = aligned_lances[-1]
            return mapping

    return {level: DEFAULT_LANCE_MAP[level] for level in levels if level in DEFAULT_LANCE_MAP}


def has_complete_lance_map(levels: list[float], mapping: dict[float, int]) -> bool:
    return bool(levels) and all(level in mapping for level in levels)


def request_lance_map(levels: list[float]) -> dict[float, int]:
    suggestions = build_default_lance_map(levels)
    result: dict[float, int] = {}
    cancelled = False

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    dialog = tk.Toplevel(root)
    dialog.title("Mapeamento de lances ARMPIL")
    dialog.attributes("-topmost", True)
    dialog.resizable(False, False)

    container = ttk.Frame(dialog, padding=14)
    container.grid(sticky="nsew")

    ttk.Label(
        container,
        text="Associe cada nivel superior ao numero do lance correspondente.",
    ).grid(row=0, column=0, columnspan=3, sticky="w")
    ttk.Label(
        container,
        text="Cada trecho do pilar entra na tabela pelo lance imediatamente acima.",
    ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))
    ttk.Label(
        container,
        text="O mesmo numero de lance pode ser repetido em mais de um nivel.",
    ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 10))

    entry_vars: dict[float, tk.StringVar] = {}
    for offset, level in enumerate(levels):
        row_index = offset + 3
        prev_level = levels[offset - 1] if offset > 0 else None
        if prev_level is None:
            context = "Trecho logo abaixo"
        else:
            context = f"Trecho {format_level(prev_level)} -> {format_level(level)}"

        ttk.Label(container, text=format_level(level), width=12).grid(row=row_index, column=0, sticky="w", padx=(0, 8))
        ttk.Label(container, text=context, width=24).grid(row=row_index, column=1, sticky="w", padx=(0, 8))
        default_value = "" if level not in suggestions else str(suggestions[level])
        var = tk.StringVar(value=default_value)
        ttk.Entry(container, width=10, textvariable=var).grid(row=row_index, column=2, sticky="w")
        entry_vars[level] = var

    button_row = len(levels) + 3

    def submit() -> None:
        pending: dict[float, int] = {}
        for level, var in entry_vars.items():
            text = var.get().strip()
            if not text:
                continue
            try:
                pending[level] = int(text)
            except ValueError:
                messagebox.showerror(
                    "Valor invalido",
                    f"Lance invalido para o nivel {format_level(level)}.",
                    parent=dialog,
                )
                return

        result.clear()
        result.update(pending)
        dialog.destroy()

    def cancel() -> None:
        nonlocal cancelled
        cancelled = True
        dialog.destroy()

    ttk.Button(container, text="Confirmar", command=submit).grid(row=button_row, column=1, sticky="e", pady=(12, 0))
    ttk.Button(container, text="Cancelar", command=cancel).grid(row=button_row, column=2, sticky="w", pady=(12, 0))

    dialog.protocol("WM_DELETE_WINDOW", cancel)
    dialog.transient(root)
    dialog.grab_set()
    dialog.update_idletasks()
    dialog.deiconify()
    dialog.lift()
    dialog.focus_force()
    dialog.wait_window()
    root.destroy()

    if cancelled:
        sys.exit("[CANCELADO] Mapeamento de lances nao informado.")
    return result


def normalize_longitudinal_diameter(diam: float) -> float:
    if diam < BITOLA_MIN_LONG:
        return diam
    return min(ALLOWED_LONGITUDINAL_DIAMETERS, key=lambda allowed: (abs(allowed - diam), allowed))


def find_level_above_bar(y_bar: float, levels: list[dict]) -> dict | None:
    """Return the upper level that bounds the bar in PDF coordinates."""

    above = [level for level in levels if level["y"] < y_bar]
    if above:
        return max(above, key=lambda level: level["y"])

    below = [level for level in levels if level["y"] >= y_bar]
    if below:
        return min(below, key=lambda level: level["y"])
    return None


def get_box_rebar_segments(box: dict, vertical_lines: list[dict] | None) -> list[dict]:
    if not vertical_lines or not box.get("levels"):
        return []

    cached = box.get("_rebar_segments")
    if cached is not None:
        return cached

    frame_xs = {
        round(x, 1)
        for line in box.get("_division_lines", [])
        for x in (line["x0"], line["x1"])
    }
    if box.get("_division_lines"):
        division_left = min(line["x0"] for line in box["_division_lines"])
        division_right = max(line["x1"] for line in box["_division_lines"])
    else:
        division_left = box["x_left"]
        division_right = box["x_right"]

    left_limit = min(box["x_left"], division_left) - REBAR_DIVISION_X_PAD
    right_limit = max(box["x_right"], division_right) + REBAR_DIVISION_X_PAD
    y_min = box["cy"] - 100
    y_max = max(level.get("line_y", level["y"]) for level in box["levels"]) + LOWEST_LEVEL_EXTRA_Y
    max_reasonable_length = (y_max - y_min) + 20

    segments = [
        segment
        for segment in vertical_lines
        if left_limit <= segment["x"] <= right_limit
        and all(abs(segment["x"] - frame_x) > REBAR_RIGHT_BORDER_TOL for frame_x in frame_xs)
        and segment["length"] <= max_reasonable_length
        and y_min <= segment["y1"]
        and segment["y0"] <= y_max
    ]
    box["_rebar_segments"] = segments
    return segments


def segment_crosses_level_line(segment: dict, level: dict) -> bool:
    line_y = level.get("line_y", level["y"])
    return segment["y0"] - LEVEL_LINE_TOL_Y <= line_y <= segment["y1"] + LEVEL_LINE_TOL_Y


def segment_touches_level_line(segment: dict, level: dict) -> bool:
    line_y = level.get("line_y", level["y"])
    return abs(segment["y0"] - line_y) <= LEVEL_LINE_TOL_Y or abs(segment["y1"] - line_y) <= LEVEL_LINE_TOL_Y


def get_box_rotated_labels(spans: list[dict], box: dict, vertical_lines: list[dict] | None) -> list[dict]:
    cached = box.get("_rotated_labels")
    if cached is not None:
        return cached

    segments = get_box_rebar_segments(box, vertical_lines)
    if not segments:
        box["_rotated_labels"] = []
        return []

    x_min = min(segment["x"] for segment in segments) - 50
    x_max = max(segment["x"] for segment in segments) + 50
    y_min = box["cy"] - 100
    y_max = max(level.get("line_y", level["y"]) for level in box["levels"]) + LOWEST_LEVEL_EXTRA_Y

    labels = [
        span
        for span in spans
        if RE_PX.match(span["t"])
        and abs(abs(span["ang"]) - 90) <= 8
        and x_min <= span["cx"] <= x_max
        and y_min <= span["cy"] <= y_max
    ]
    box["_rotated_labels"] = labels
    return labels


def rotated_label_confirms_lance_bar(
    spans: list[dict],
    box: dict,
    vertical_lines: list[dict] | None,
    token: str,
    row_y: float,
    level: dict,
) -> bool:
    if not vertical_lines:
        return True

    labels = [label for label in get_box_rotated_labels(spans, box, vertical_lines) if label["t"] == token]
    if not labels:
        return True

    best_distance = min(abs(label["cy"] - row_y) for label in labels)
    labels = [label for label in labels if abs(label["cy"] - row_y) <= best_distance + 5]

    segments = get_box_rebar_segments(box, vertical_lines)
    for label in labels:
        for segment in segments:
            if abs(segment["x"] - label["cx"]) > ROTATED_LABEL_SEGMENT_TOL_X:
                continue
            if not (segment["y0"] - ROTATED_LABEL_SEGMENT_TOL_Y <= label["cy"] <= segment["y1"] + ROTATED_LABEL_SEGMENT_TOL_Y):
                continue
            if segment_touches_level_line(segment, level):
                return True

    return False


def row_has_lance_bar_segment(row_y: float, level: dict, box: dict, vertical_lines: list[dict] | None) -> bool:
    segments = get_box_rebar_segments(box, vertical_lines)
    if not vertical_lines or not segments:
        return True

    return any(
        segment["y0"] - REBAR_ROW_TOL_Y <= row_y <= segment["y1"] + REBAR_ROW_TOL_Y
        and segment_crosses_level_line(segment, level)
        for segment in segments
    )


def extract_long_bars(
    spans: list[dict],
    box: dict,
    lance_map: dict[float, int],
    vertical_lines: list[dict] | None = None,
) -> list[tuple[int, int, float, str, bool]]:
    if not box["levels"]:
        return []

    level_xs = [level["x"] for level in box["levels"]]
    x_min = min(box["x_left"], min(level_xs) - 80)
    x_max = box["x_right"]
    y_min = box["cy"] - 80
    y_max = max(level["y"] for level in box["levels"]) + LOWEST_LEVEL_EXTRA_Y

    local = [
        span
        for span in spans
        if abs(span["ang"]) < 8 and x_min <= span["cx"] <= x_max and y_min <= span["cy"] <= y_max
    ]

    rows = group_by_y(local, tol=6)
    results: list[tuple[int, int, float, str, bool]] = []

    for row in rows:
        ordered = sorted(row, key=lambda span: span["x0"])
        has_spacing_token = any(RE_C_SLASH.match(span["t"]) for span in ordered)

        index = 0
        while index < len(ordered):
            if not RE_PX.match(ordered[index]["t"]):
                index += 1
                continue

            qty: int | None = None
            diam: float | None = None
            next_index = index + 1
            while next_index < len(ordered):
                if RE_PX.match(ordered[next_index]["t"]):
                    break
                if qty is None and RE_QTY.match(ordered[next_index]["t"]):
                    qty = int(ordered[next_index]["t"])
                elif qty is not None:
                    match = RE_PHI.match(ordered[next_index]["t"])
                    if match:
                        diam = norm(match.group(1))
                        break
                next_index += 1

            if qty is not None and diam is not None and diam >= BITOLA_MIN_LONG:
                if has_spacing_token and qty > 12:
                    index = next_index if next_index > index else index + 1
                    continue
                level = find_level_above_bar(ordered[index]["cy"], box["levels"])
                if level is not None:
                    level_key = round(level["val"], 2)
                    if level_key in lance_map and row_has_lance_bar_segment(
                        ordered[index]["cy"],
                        level,
                        box,
                        vertical_lines,
                    ):
                        confirmed = rotated_label_confirms_lance_bar(
                            spans,
                            box,
                            vertical_lines,
                            ordered[index]["t"],
                            ordered[index]["cy"],
                            level,
                        )
                        source = f"{ordered[index]['t']}@{ordered[index]['cy']:.1f}"
                        results.append(
                            (
                                lance_map[level_key],
                                qty,
                                normalize_longitudinal_diameter(diam),
                                source,
                                confirmed,
                            )
                        )

            index = next_index if next_index > index else index + 1

    return results


def filter_bar_entries(entries: list[tuple[int, int, float, str, bool]]) -> list[tuple[int, int, float, str, bool]]:
    grouped: dict[tuple[int, float], list[tuple[int, int, float, str, bool]]] = defaultdict(list)
    for entry in entries:
        lance, _qty, diam, _source, _confirmed = entry
        grouped[(lance, diam)].append(entry)

    filtered: list[tuple[int, int, float, str, bool]] = []
    for group in grouped.values():
        if len(group) > 1 and any(entry[4] for entry in group):
            filtered.extend(entry for entry in group if entry[4])
        else:
            filtered.extend(group)

    return filtered


def main() -> None:
    discover = "--discover" in sys.argv
    levels_only = "--levels" in sys.argv
    pdf_path, out_csv = choose_paths(discover)

    if not pdf_path.exists():
        sys.exit(f"[ERRO] Arquivo nao encontrado:\n  {pdf_path}")

    print(f"Lendo: {pdf_path.name}")
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    spans = get_spans(page)
    vertical_lines, horizontal_lines = get_drawing_lines(page)
    boxes = find_boxes(spans)
    assign_levels(spans, boxes)
    refine_box_bounds_by_level_rows(boxes)
    assign_levels(spans, boxes)
    attach_level_division_lines(boxes, horizontal_lines)
    doc.close()

    print(f"Boxes identificados: {len(boxes)}")

    levels = collect_unique_levels(boxes)
    if not levels:
        sys.exit("[ERRO] Nenhum nivel foi encontrado no PDF.")

    assignable_levels = collect_assignable_levels(boxes, spans, vertical_lines)
    if levels_only:
        formatted_all_levels = format_level_list(levels)
        formatted_levels = format_level_list(assignable_levels)
        print(f"LEVELS={formatted_levels}")
        print(f"ALL_LEVELS={formatted_all_levels}")
        emit_result_line(f"LEVELS={formatted_levels}")
        emit_result_line(f"ALL_LEVELS={formatted_all_levels}")
        return

    default_map = build_default_lance_map(assignable_levels)

    if discover:
        print("\n=== DISCOVER MODE ===")
        for box in boxes:
            box_levels = [(format_level(level["val"]), round(level["y"], 2)) for level in box["levels"]]
            print(f"\n  {box['raw']!r:40s} -> {box['names']}")
            print(f"    Niveis (valor, y-PDF): {box_levels}")

        print("\n=== NIVEIS UNICOS ===")
        for level in assignable_levels:
            suggestion = default_map.get(level)
            extra = f" -> sugestao de lance {suggestion}" if suggestion is not None else ""
            print(f"  {format_level(level)}{extra}")

        print("\nRode sem --discover para confirmar o mapeamento e gerar o CSV.")
        return

    automation_mode = bool(os.environ.get("ARMPIL_RESULT_FILE", "").strip())

    if not assignable_levels:
        lance_map = {}
        print("Nenhum trecho de lance com armadura longitudinal foi identificado.")
    elif has_complete_lance_map(assignable_levels, default_map):
        lance_map = {level: default_map[level] for level in assignable_levels}
        print("Mapeamento de lances aplicado automaticamente.")
    elif automation_mode:
        lance_map = default_map
        mapped_levels = ", ".join(format_level(level) for level in assignable_levels if level in lance_map)
        skipped_levels = ", ".join(format_level(level) for level in assignable_levels if level not in lance_map)
        if mapped_levels:
            print(f"Mapeamento parcial aplicado: {mapped_levels}")
        if skipped_levels:
            print(f"Niveis ignorados: {skipped_levels}")
    else:
        lance_map = request_lance_map(assignable_levels)

    raw_rows: dict[tuple[str, int], list[tuple[int, float, str]]] = defaultdict(list)
    for box in boxes:
        data = filter_bar_entries(extract_long_bars(spans, box, lance_map, vertical_lines))
        for lance, qty, diam, source, _confirmed in data:
            for name in box["names"]:
                raw_rows[(name, lance)].append((qty, diam, source))

    all_rows: list[tuple[str, int, int, str, str]] = []
    ordered_keys = sorted(raw_rows, key=lambda item: (pillar_sort_key(item[0]), item[1]))
    for pilar, lance in ordered_keys:
        entries = list(dict.fromkeys(raw_rows[(pilar, lance)]))
        by_diam: dict[float, int] = defaultdict(int)
        for qty, diam, _source in entries:
            by_diam[diam] += qty

        for diam in sorted(by_diam):
            qty = by_diam[diam]
            all_rows.append((pilar, lance, qty, fmt_num(diam), f"{calc_as(qty, diam):.2f}"))

    if out_csv is None:
        sys.exit("[ERRO] Caminho de saida do CSV nao definido.")

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(["Pilar", "Lance", "Qtd(Qf)", "Bitola(mm)", "As Total (cm2)"])
        writer.writerows(all_rows)

    print(f"[OK] {len(all_rows)} registros -> {out_csv}")
    print(f"CSV_OUTPUT={out_csv}")
    emit_result_line(f"CSV_OUTPUT={out_csv}")

    if all_rows:
        print("\nPrimeiras 10 linhas:")
        print("Pilar;Lance;Qtd;Bitola;As")
        for row in all_rows[:10]:
            print(f"  {row[0]};{row[1]};{row[2]};{row[3]};{row[4]}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        message = str(exc)
        if message:
            print(message)
            emit_result_line(message)
        raise
    except Exception:
        message = traceback.format_exc()
        print(message, file=sys.stderr)
        emit_result_line("[ERROPY] " + message.strip())
        raise
