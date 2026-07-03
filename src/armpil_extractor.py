#!/usr/bin/env python3
"""
armpil_extractor.py - Extracao ARMPIL PDF -> CSV

Extrai armadura longitudinal de pranchas ARMPIL (TQS/Eberick/AltoQi)
por leitura posicional de texto vetorial no PDF.

Dependencias: pip install PyMuPDF rapidocr_onnxruntime pillow
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
TITLE_ROW_TOL_Y = 70.0
OCR_RENDER_SCALE = 2.5
OCR_TILE_SIZE = 1800
OCR_TILE_OVERLAP = 250
OCR_TITLE_MAX_X_RATIO = 0.82
OCR_STRUCTURAL_Y_PAD = 1050.0
OCR_STRUCTURAL_X_PAD = 220.0
OCR_MIN_STRUCTURAL_TOKENS = 3
OCR_LOCAL_SCALE = 5.0
OCR_STRIP_SCALE = 6.0
OCR_LOCAL_X_PAD_LEFT = 60.0
OCR_LOCAL_X_PAD_RIGHT = 170.0
OCR_LOCAL_Y_PAD_BOTTOM = 1150.0
OCR_BAND_STRIP_X_PAD_LEFT = 5.0
OCR_BAND_STRIP_X_PAD_RIGHT = 150.0
OCR_BAND_STRIP_Y_PAD = 10.0
OCR_LEVEL_ROW_TOL_Y = 18.0
LEVEL_COLUMN_PAD_X = 12.0

# Historical defaults for recurring jobs. The user can confirm or override
# them in the level mapping dialog before the CSV is generated.
DEFAULT_LANCE_MAP: dict[float, int] = {
    1040.25: 0,
    1043.40: 6,
    1046.60: 7,
    1050.35: 8,
    1050.95: 8,
    1051.00: 8,
    1055.91: 10,
    1059.11: 11,
    1062.31: 12,
    1065.51: 13,
    1068.71: 14,
    1071.91: 15,
}

RE_NIVEL = re.compile(r"^\+?(\d{3,4}[,.]\d{1,2})$")
RE_PX = re.compile(r"^(P[A-Z]*)(\d+)([A-Z]*)$", re.I)
RE_QTY = re.compile(r"^\d{1,3}$")
RE_PHI = re.compile(r"^[O\u00D8\u2205\u03A6\u03C6]\s*(\d+[,.]?\d*)$", re.I)
RE_C_SLASH = re.compile(r"^C/")
RE_TITLE_PART = re.compile(r"((?:P[A-Z]*)\d+[A-Z]*)(?:\s*\([^)]*\))?", re.I)
RE_PILAR_SORT = re.compile(r"^(P[A-Z]*)(\d+)([A-Z]*)$", re.I)
RE_STRUCTURAL_TOKEN = re.compile(
    r"(?:[O\u00D8\u2205\u03A6\u03C6]\s*\d|C/|C=|FUNDA|LAJE|^N\d+|^\d+\s*[X\u00D7]\s*\d+)",
    re.I,
)
RE_LEVEL_DIGIT = re.compile(r"(\d)\s*A", re.I)
RE_OCR_LONG_TOKEN = re.compile(
    r"(\d{1,2}(?:\s*[X\u00D7]\s*\d{1,2})?)\s*[\u00D8\u2205\u03A6\u03C6]\s*(10|12(?:[,.]5)?|16|20|25|32)\b",
    re.I,
)
RE_OCR_COMBINED_LONG = re.compile(r"^(\d{1,2})(10|125|16|20|25|32)$")
RE_OCR_C_LENGTH = re.compile(r"C\s*[=:\-]?\s*(\d{2,4})", re.I)


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

    # Bridge run (VBA): the CSV is only an intermediate hand-off to fill the
    # ARMPIL table in Excel, so it goes to a temp folder and the caller
    # deletes it once the table has been populated.
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
    return qty * math.pi * (d_cm / 2) ** 2


def fmt_num(val: float) -> str:
    if float(val).is_integer():
        return str(int(val))
    return f"{val:.2f}".rstrip("0").rstrip(".")


def normalize_level_key(level: float | str) -> str:
    if isinstance(level, str):
        text = " ".join(level.replace("_", " ").strip().upper().split())
        return text
    return f"{float(level):.2f}"


def level_sort_key(level: float | str) -> tuple[int, float, str]:
    if isinstance(level, str):
        token = normalize_level_key(level)
        if token == "FUNDACAO":
            return (0, 0.0, token)
        match = RE_LEVEL_DIGIT.search(token)
        if match:
            return (1, float(match.group(1)), token)
        return (2, 0.0, token)
    return (1, float(level), f"{float(level):.2f}")


def sort_level_values(levels: list[float | str]) -> list[float | str]:
    return sorted(levels, key=level_sort_key)


def format_level(level: float | str) -> str:
    if isinstance(level, str):
        return normalize_level_key(level)
    return f"+{level:.2f}"


def format_level_list(levels: list[float | str]) -> str:
    values = []
    for level in levels:
        if isinstance(level, str):
            values.append(normalize_level_key(level))
        else:
            values.append(f"{float(level):.2f}")
    return ",".join(values)


def parse_names(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text)
    names = [match.group(1).upper() for match in RE_TITLE_PART.finditer(normalized)]
    return list(dict.fromkeys(names))


def pillar_sort_key(name: str) -> tuple[int, int, str, str, str]:
    text = name.strip().upper()
    match = RE_PILAR_SORT.match(text)
    if not match:
        return (10**9, 10, text, text)

    prefix, number, suffix = match.groups()
    prefix_rank = 0 if prefix.upper() == "P" else 1
    return (int(number), prefix_rank, prefix, suffix or "", text)


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


def dedupe_ocr_spans(spans: list[dict]) -> list[dict]:
    if not spans:
        return []

    deduped: list[dict] = []
    for span in sorted(
        spans,
        key=lambda item: (
            item["t"],
            round(item["cx"], 1),
            round(item["cy"], 1),
            -item.get("score", 0.0),
        ),
    ):
        duplicate = next(
            (
                existing
                for existing in deduped
                if existing["t"] == span["t"]
                and abs(existing["cx"] - span["cx"]) <= 8
                and abs(existing["cy"] - span["cy"]) <= 8
                and abs(existing["w"] - span["w"]) <= 10
                and abs((existing["y1"] - existing["y0"]) - (span["y1"] - span["y0"])) <= 10
            ),
            None,
        )
        if duplicate is None:
            deduped.append(span)
            continue

        if span.get("score", 0.0) > duplicate.get("score", 0.0):
            duplicate.update(span)

    return deduped


def get_ocr_spans(page) -> list[dict]:
    try:
        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return []

    pix = page.get_pixmap(matrix=fitz.Matrix(OCR_RENDER_SCALE, OCR_RENDER_SCALE), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    page_width = float(page.rect.width)
    page_height = float(page.rect.height)

    tile_step = max(1, OCR_TILE_SIZE - OCR_TILE_OVERLAP)
    detector = RapidOCR()
    spans: list[dict] = []

    for top in range(0, image.height, tile_step):
        for left in range(0, image.width, tile_step):
            crop = image.crop((left, top, min(left + OCR_TILE_SIZE, image.width), min(top + OCR_TILE_SIZE, image.height)))
            result, _ = detector(np.array(crop))
            if not result:
                continue

            for box, text, score in result:
                normalized = unicodedata.normalize("NFKC", text).strip()
                if not normalized:
                    continue

                xs = [point[0] for point in box]
                ys = [point[1] for point in box]
                x0 = (min(xs) + left) / OCR_RENDER_SCALE
                x1 = (max(xs) + left) / OCR_RENDER_SCALE
                y0 = (min(ys) + top) / OCR_RENDER_SCALE
                y1 = (max(ys) + top) / OCR_RENDER_SCALE
                x0 = max(0.0, min(x0, page_width))
                x1 = max(0.0, min(x1, page_width))
                y0 = max(0.0, min(y0, page_height))
                y1 = max(0.0, min(y1, page_height))
                if x1 <= x0 or y1 <= y0:
                    continue

                spans.append(
                    {
                        "t": normalized,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "w": x1 - x0,
                        "cx": (x0 + x1) / 2,
                        "cy": (y0 + y1) / 2,
                        "sz": y1 - y0,
                        "ang": 0.0,
                        "ocr": True,
                        "score": float(score),
                    }
                )

    return dedupe_ocr_spans(spans)


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


def attach_box_bounds(boxes: list[dict], tol: float = TITLE_ROW_TOL_Y) -> None:
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
                "ocr": any(part.get("ocr") for part in parts),
            }
        )
    return boxes


def box_has_structural_context(box: dict, spans: list[dict]) -> bool:
    if not box.get("ocr"):
        return True

    page_width = max((span["x1"] for span in spans), default=0.0)
    if page_width and box["cx"] > page_width * OCR_TITLE_MAX_X_RATIO:
        return False

    matches = [
        span
        for span in spans
        if box["x0"] - OCR_STRUCTURAL_X_PAD <= span["cx"] <= box["x1"] + OCR_STRUCTURAL_X_PAD
        and box["cy"] + 10 <= span["cy"] <= box["cy"] + OCR_STRUCTURAL_Y_PAD
        and RE_STRUCTURAL_TOKEN.search(span["t"])
    ]
    return len(matches) >= OCR_MIN_STRUCTURAL_TOKENS


def find_boxes(spans: list[dict]) -> list[dict]:
    candidates = []
    for span in spans:
        if span.get("ocr"):
            if not parse_names(span["t"]):
                continue
        else:
            if abs(span["sz"] - 15.5) > 1.2:
                continue
            if abs(span["ang"]) > 5:
                continue
            if not parse_names(span["t"]):
                continue
        if abs(span["ang"]) > 5:
            continue
        candidates.append(span)

    boxes = merge_title_candidates(candidates)
    boxes = [box for box in boxes if box_has_structural_context(box, spans)]
    boxes.sort(key=lambda box: (round(box["cy"] / 50) * 50, box["cx"]))
    attach_box_bounds(boxes)
    return boxes


def median_value(values: list[float]) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def keep_dominant_level_x_cluster(
    levels: list[dict],
    box_cx: float,
    box_cy: float,
    preferred_keys: set[tuple[float, float, float]] | None = None,
    tol_x: float = 45.0,
) -> list[dict]:
    if len(levels) <= 1:
        return levels

    clusters: list[list[dict]] = []
    for level in sorted(levels, key=lambda item: item["x"]):
        for cluster in clusters:
            center_x = sum(item["x"] for item in cluster) / len(cluster)
            if abs(level["x"] - center_x) <= tol_x:
                cluster.append(level)
                break
        else:
            clusters.append([level])

    def cluster_score(cluster: list[dict]) -> tuple[int, int, float]:
        preferred_count = 0
        if preferred_keys:
            preferred_count = sum(
                1
                for level in cluster
                if (round(level["val"], 2), round(level["x"], 2), round(level["y"], 2)) in preferred_keys
            )
        center_x = sum(item["x"] for item in cluster) / len(cluster)
        top_y = min(item["y"] for item in cluster)
        return (preferred_count, -abs(top_y - box_cy), len(cluster), -abs(center_x - box_cx))

    best = max(clusters, key=cluster_score)
    return sorted(best, key=lambda item: item["y"])


def keep_contiguous_level_sequence(levels: list[dict]) -> list[dict]:
    ordered = sorted(levels, key=lambda item: item["y"])
    if len(ordered) <= 1:
        return ordered

    gaps = [
        current["y"] - previous["y"]
        for previous, current in zip(ordered, ordered[1:])
        if current["y"] > previous["y"]
    ]
    typical_gap = median_value(gaps)
    if typical_gap is None:
        return ordered

    # Level rows usually form a regular vertical cadence. Preserve the
    # contiguous run and stop when the next candidate is far below it.
    max_gap = max(LOWEST_LEVEL_EXTRA_Y + 80.0, typical_gap * 2.2)
    contiguous = [ordered[0]]
    direction: int | None = None
    for previous, current in zip(ordered, ordered[1:]):
        if current["y"] - previous["y"] > max_gap:
            break
        delta_value = current["val"] - previous["val"]
        if abs(delta_value) > SAME_LANCE_LEVEL_TOL:
            current_direction = -1 if delta_value < 0 else 1
            if direction is None:
                direction = current_direction
            elif current_direction != direction:
                break
        contiguous.append(current)
    return contiguous


def assign_levels(spans: list[dict], boxes: list[dict]) -> None:
    level_spans = []
    for span in spans:
        if not span.get("ocr") and abs(span["sz"] - 11.7) > 0.8:
            continue
        if abs(span["ang"]) > 5:
            continue
        match = RE_NIVEL.match(span["t"])
        if not match:
            continue
        level_spans.append({"val": norm(match.group(1)), "x": span["cx"], "y": span["cy"]})

    for box in boxes:
        y_lo = box["cy"] - 50
        base_y_hi = box["cy"] + 650
        column_candidates = [
            level
            for level in level_spans
            if box["x_left"] - LEVEL_COLUMN_PAD_X <= level["x"] <= box["x_right"] + LEVEL_COLUMN_PAD_X
            and y_lo <= level["y"]
        ]
        base_nearby = [
            level for level in column_candidates if level["y"] <= base_y_hi
        ]

        nearby = base_nearby
        if base_nearby:
            base_keys = {
                (round(level["val"], 2), round(level["x"], 2), round(level["y"], 2))
                for level in base_nearby
            }
            dominant_cluster = keep_dominant_level_x_cluster(column_candidates, box["cx"], box["cy"], base_keys)
            contiguous_candidates = keep_contiguous_level_sequence(dominant_cluster)
            nearby = [
                {
                    "val": level["val"],
                    "x": level["x"],
                    "y": level["y"],
                    "base_rank": 0
                    if (round(level["val"], 2), round(level["x"], 2), round(level["y"], 2))
                    in base_keys
                    else 1,
                }
                for level in contiguous_candidates
            ]

        seen: dict[float, dict] = {}
        for level in sorted(
            nearby,
            key=lambda item: (
                item["val"],
                item.get("base_rank", 0),
                abs(item["x"] - box["cx"]),
                item["y"],
            ),
        ):
            key = round(level["val"], 2)
            if key not in seen:
                seen[key] = {"val": level["val"], "x": level["x"], "y": level["y"]}

        box["levels"] = sorted(seen.values(), key=lambda item: item["y"], reverse=True)


def fill_missing_consensus_levels(boxes: list[dict]) -> None:
    if len(boxes) < 2:
        return

    level_samples: dict[float, list[dict]] = defaultdict(list)
    for box in boxes:
        for level in box.get("levels", []):
            if isinstance(level["val"], str):
                continue
            level_samples[round(level["val"], 2)].append(level)

    consensus_threshold = max(2, len(boxes) - 1)
    consensus_levels: list[dict] = []
    for key, samples in level_samples.items():
        if len(samples) < consensus_threshold:
            continue
        y_values = [sample["y"] for sample in samples]
        x_values = [sample["x"] for sample in samples]
        consensus_levels.append(
            {
                "key": key,
                "val": median_value([sample["val"] for sample in samples]) or samples[0]["val"],
                "x": median_value(x_values) or samples[0]["x"],
                "y": median_value(y_values) or samples[0]["y"],
            }
        )

    if not consensus_levels:
        return

    for box in boxes:
        levels = box.get("levels", [])
        if len(levels) < 2:
            continue

        present_keys = {round(level["val"], 2) for level in levels if not isinstance(level["val"], str)}
        ordered = sorted(levels, key=lambda item: item["y"])
        gaps = [
            current["y"] - previous["y"]
            for previous, current in zip(ordered, ordered[1:])
            if current["y"] > previous["y"]
        ]
        typical_gap = median_value(gaps)
        if typical_gap is None:
            continue

        top_y = ordered[0]["y"]
        bottom_y = ordered[-1]["y"]
        reference_x = median_value([level["x"] for level in levels]) or box["cx"]
        additions: list[dict] = []

        for consensus in consensus_levels:
            if consensus["key"] in present_keys:
                continue

            if consensus["y"] < top_y and top_y - consensus["y"] <= typical_gap * 1.35:
                additions.append({"val": consensus["val"], "x": reference_x, "y": consensus["y"]})
            elif consensus["y"] > bottom_y and consensus["y"] - bottom_y <= typical_gap * 1.35:
                additions.append({"val": consensus["val"], "x": reference_x, "y": consensus["y"]})

        if additions:
            box["levels"] = sorted(levels + additions, key=lambda item: item["y"], reverse=True)


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

            box["x_left"] = max(box["x_left"], left)
            box["x_right"] = min(box["x_right"], right)
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


def collect_unique_levels(boxes: list[dict]) -> list[float | str]:
    values: dict[str, float | str] = {}
    for box in boxes:
        for level in box.get("levels", []):
            key = normalize_level_key(level["val"])
            values.setdefault(key, level["val"])
    return sort_level_values(list(values.values()))


def collect_assignable_levels(
    boxes: list[dict],
    spans: list[dict],
    vertical_lines: list[dict] | None = None,
) -> list[float | str]:
    named_levels: dict[str, float | str] = {}
    for box in boxes:
        for level_name, _qty, _diam, _source, _confirmed in box.get("_named_longitudinal_entries", []):
            for level in box.get("levels", []):
                if normalize_level_key(level["val"]) == normalize_level_key(level_name):
                    named_levels.setdefault(normalize_level_key(level_name), level["val"])
                    break
    if named_levels:
        return sort_level_values(list(named_levels.values()))

    levels = collect_unique_levels(boxes)
    probe_map = {normalize_level_key(level): index for index, level in enumerate(levels, start=1)}
    level_by_probe = {index: level for level, index in probe_map.items()}

    values: dict[str, float | str] = {}
    for box in boxes:
        for lance, _qty, _diam, _source, _confirmed in extract_long_bars(spans, box, probe_map, vertical_lines):
            if lance in level_by_probe:
                level_value = level_by_probe[lance]
                values[normalize_level_key(level_value)] = level_value

    return sort_level_values(list(values.values()))


def parse_env_lance_map() -> dict[str, int]:
    raw = os.environ.get("ARMPIL_LANCE_MAP", "").strip()
    if not raw:
        return {}

    mapping: dict[str, int] = {}
    for chunk in re.split(r"[;\n]+", raw):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        level_text, lance_text = chunk.split("=", 1)
        try:
            normalized = normalize_level_key(level_text if not re.fullmatch(r"\+?\d+[,.]?\d*", level_text.strip()) else norm(level_text))
            mapping[normalized] = int(lance_text.strip())
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


def read_known_pilar_lances_from_env() -> dict[str, list[int]]:
    raw = os.environ.get("ARMPIL_KNOWN_PILAR_LANCES", "").strip()
    if not raw:
        return {}

    mapping: dict[str, list[int]] = {}
    for chunk in re.split(r"[;\n]+", raw):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        name_text, lances_text = chunk.split("=", 1)
        name = name_text.strip().upper()
        if not name:
            continue
        values: list[int] = []
        for token in re.split(r"[,\s]+", lances_text.strip()):
            token = token.strip()
            if not token:
                continue
            try:
                values.append(int(token))
            except ValueError:
                continue
        if values:
            mapping[name] = sorted(dict.fromkeys(values))

    return mapping


def collect_known_lances_for_boxes(boxes: list[dict]) -> list[int]:
    mapping = read_known_pilar_lances_from_env()
    if not mapping:
        return []

    values: list[int] = []
    for box in boxes:
        for name in box.get("names", []):
            values.extend(mapping.get(name.strip().upper(), []))
    return sorted(dict.fromkeys(values))


def align_known_lances_to_levels(known_lances: list[int], level_count: int) -> list[int]:
    if level_count <= 0 or not known_lances:
        return []
    if len(known_lances) <= level_count:
        return known_lances
    return known_lances[-level_count:]


def get_default_lance_for_level(level: float | str) -> int | None:
    numeric_level: float | None

    if isinstance(level, str):
        text = level.strip()
        if not re.fullmatch(r"\+?\d+[,.]?\d*", text):
            return None
        try:
            numeric_level = norm(text)
        except ValueError:
            return None
    else:
        numeric_level = float(level)

    return DEFAULT_LANCE_MAP.get(numeric_level)


def build_default_lance_map(levels: list[float | str], known_lances: list[int] | None = None) -> dict[str, int]:
    env_map = parse_env_lance_map()
    if env_map:
        return {
            normalize_level_key(level): env_map[normalize_level_key(level)]
            for level in levels
            if normalize_level_key(level) in env_map
        }

    default_mapping: dict[str, int] = {}
    for level in levels:
        lance = get_default_lance_for_level(level)
        if lance is not None:
            default_mapping[normalize_level_key(level)] = lance
    if has_complete_lance_map(levels, default_mapping):
        return default_mapping

    ordered_levels = sort_level_values(levels)
    if known_lances is None:
        known_lances = read_known_lances_from_env()
    aligned_lances = align_known_lances_to_levels(known_lances, len(ordered_levels))
    if aligned_lances:
        mapping = {normalize_level_key(level): lance for level, lance in zip(ordered_levels, aligned_lances)}
        if len(aligned_lances) == len(ordered_levels):
            return mapping

        last_level = ordered_levels[len(aligned_lances) - 1]
        trailing_levels = ordered_levels[len(aligned_lances) :]
        if trailing_levels and not isinstance(last_level, str) and all(
            not isinstance(level, str) and level - last_level <= SAME_LANCE_LEVEL_TOL
            for level in trailing_levels
        ):
            for level in trailing_levels:
                mapping[normalize_level_key(level)] = aligned_lances[-1]
            return mapping

    return default_mapping


def get_first_positive_lance(levels: list[float | str], mapping: dict[str, int]) -> int | None:
    for level in levels:
        lance = mapping.get(normalize_level_key(level))
        if isinstance(lance, int) and lance > 0:
            return lance
    return None


def shift_lance_map_start(levels: list[float | str], mapping: dict[str, int], desired_start: int) -> dict[str, int]:
    current_start = get_first_positive_lance(levels, mapping)
    if current_start is None:
        raise ValueError("Nenhum lance positivo disponivel para ajustar.")

    offset = desired_start - current_start
    shifted: dict[str, int] = {}
    for level in levels:
        level_key = normalize_level_key(level)
        if level_key not in mapping:
            continue
        lance = mapping[level_key]
        if lance > 0:
            shifted[level_key] = lance + offset
        else:
            shifted[level_key] = lance
    return shifted


def has_complete_lance_map(levels: list[float | str], mapping: dict[str, int]) -> bool:
    return bool(levels) and all(normalize_level_key(level) in mapping for level in levels)


def request_lance_map(levels: list[float | str]) -> dict[str, int]:
    suggestions = build_default_lance_map(levels)
    result: dict[str, int] = {}
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

    suggested_start = get_first_positive_lance(levels, suggestions)
    start_var = tk.StringVar(value="" if suggested_start is None else str(suggested_start))
    ttk.Label(container, text="Primeiro lance", width=12).grid(row=3, column=0, sticky="w", padx=(0, 8))
    ttk.Label(container, text="Desloca toda a sequencia sugerida", width=24).grid(row=3, column=1, sticky="w", padx=(0, 8))
    ttk.Entry(container, width=10, textvariable=start_var).grid(row=3, column=2, sticky="w")

    entry_vars: dict[float, tk.StringVar] = {}
    for offset, level in enumerate(levels):
        row_index = offset + 4
        prev_level = levels[offset - 1] if offset > 0 else None
        if prev_level is None:
            context = "Trecho logo abaixo"
        else:
            context = f"Trecho {format_level(prev_level)} -> {format_level(level)}"

        ttk.Label(container, text=format_level(level), width=12).grid(row=row_index, column=0, sticky="w", padx=(0, 8))
        ttk.Label(container, text=context, width=24).grid(row=row_index, column=1, sticky="w", padx=(0, 8))
        level_key = normalize_level_key(level)
        default_value = "" if level_key not in suggestions else str(suggestions[level_key])
        var = tk.StringVar(value=default_value)
        ttk.Entry(container, width=10, textvariable=var).grid(row=row_index, column=2, sticky="w")
        entry_vars[level] = var

    def apply_start_lance() -> None:
        text = start_var.get().strip()
        if not text:
            return
        try:
            desired_start = int(text)
        except ValueError:
            messagebox.showerror("Valor invalido", "Informe um numero inteiro para o primeiro lance.", parent=dialog)
            return
        if desired_start <= 0:
            messagebox.showerror("Valor invalido", "O primeiro lance deve ser maior que zero.", parent=dialog)
            return

        current_values: dict[str, int] = {}
        for level, var in entry_vars.items():
            value = var.get().strip()
            if not value:
                continue
            try:
                current_values[normalize_level_key(level)] = int(value)
            except ValueError:
                messagebox.showerror(
                    "Valor invalido",
                    f"Lance invalido para o nivel {format_level(level)}.",
                    parent=dialog,
                )
                return

        try:
            shifted = shift_lance_map_start(levels, current_values, desired_start)
        except ValueError as exc:
            messagebox.showerror("Ajuste indisponivel", str(exc), parent=dialog)
            return

        if any(lance < 0 for lance in shifted.values()):
            messagebox.showerror(
                "Valor invalido",
                "O ajuste informado gerou lances negativos.",
                parent=dialog,
            )
            return

        for level in levels:
            level_key = normalize_level_key(level)
            if level_key in shifted:
                entry_vars[level].set(str(shifted[level_key]))

    ttk.Button(container, text="Aplicar", command=apply_start_lance).grid(row=3, column=3, sticky="w")

    button_row = len(levels) + 4

    def submit() -> None:
        pending: dict[str, int] = {}
        for level, var in entry_vars.items():
            text = var.get().strip()
            if not text:
                continue
            try:
                pending[normalize_level_key(level)] = int(text)
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


def parse_ocr_qty_token(text: str) -> int | None:
    cleaned = text.replace(" ", "").replace("\u00D7", "x").replace("X", "x")
    if not cleaned:
        return None
    if "x" in cleaned:
        left, right = cleaned.split("x", 1)
        if left.isdigit() and right.isdigit():
            return int(left) * int(right)
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None
    return int(digits)


def normalize_ocr_text(text: str) -> str:
    cleaned = unicodedata.normalize("NFKC", text).upper()
    cleaned = cleaned.replace("Ø", "Φ").replace("∅", "Φ").replace("O", "O")
    cleaned = cleaned.replace("¥", "Φ").replace("$", "Φ").replace("¢", "Φ")
    cleaned = cleaned.replace("?", "Φ")
    cleaned = " ".join(cleaned.split())
    return cleaned


def extract_long_matches_from_text(text: str) -> list[tuple[int, float]]:
    matches: list[tuple[int, float]] = []
    normalized = normalize_ocr_text(text)

    for qty_text, diam_text in RE_OCR_LONG_TOKEN.findall(normalized):
        qty = parse_ocr_qty_token(qty_text)
        if qty is None:
            continue
        diam = float(diam_text.replace(",", "."))
        if diam >= BITOLA_MIN_LONG:
            matches.append((qty, diam))

    compact = normalized.replace(" ", "")
    combined = RE_OCR_COMBINED_LONG.match(compact)
    if combined:
        qty = int(combined.group(1))
        diam_code = combined.group(2)
        diam = 12.5 if diam_code == "125" else float(diam_code)
        if diam >= BITOLA_MIN_LONG:
            matches.append((qty, diam))

    return matches


def get_crop_ocr_lines(page, clip: fitz.Rect, scale: float, rotate_degrees: int = 0) -> list[dict]:
    try:
        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return []

    if clip.x1 <= clip.x0 or clip.y1 <= clip.y0:
        return []

    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    original_width, original_height = image.size

    if rotate_degrees:
        image = image.rotate(rotate_degrees, expand=True)

    detector = RapidOCR()
    result, _ = detector(np.array(image))
    if not result:
        return []

    lines: list[dict] = []
    for box, text, score in result:
        normalized = unicodedata.normalize("NFKC", text).strip()
        if not normalized:
            continue

        xs = [point[0] for point in box]
        ys = [point[1] for point in box]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2

        if rotate_degrees == 270:
            page_x = cy / scale + clip.x0
            page_y = (original_height - cx) / scale + clip.y0
        elif rotate_degrees == 90:
            page_x = (original_width - cy) / scale + clip.x0
            page_y = cx / scale + clip.y0
        else:
            page_x = cx / scale + clip.x0
            page_y = cy / scale + clip.y0

        lines.append(
            {
                "t": normalized,
                "cx": page_x,
                "cy": page_y,
                "score": float(score),
            }
        )

    return lines


def find_level_above_bar(y_bar: float, levels: list[dict]) -> dict | None:
    """Return the upper level that bounds the bar in PDF coordinates."""

    above = [level for level in levels if level["y"] < y_bar]
    if above:
        return max(above, key=lambda level: level["y"])

    below = [level for level in levels if level["y"] >= y_bar]
    if below:
        return max(below, key=lambda level: level_sort_key(level["val"]))
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


def detect_named_levels(page, boxes: list[dict]) -> list[tuple[str, float]]:
    candidate_rows: list[tuple[float, str]] = []

    for box in boxes:
        clip = fitz.Rect(
            max(0.0, box["x0"] - OCR_LOCAL_X_PAD_LEFT),
            max(0.0, box["cy"] + 20.0),
            min(page.rect.width, box["x1"] + OCR_LOCAL_X_PAD_RIGHT),
            min(page.rect.height, box["cy"] + OCR_LOCAL_Y_PAD_BOTTOM),
        )
        lines = get_crop_ocr_lines(page, clip, OCR_LOCAL_SCALE)
        if not lines:
            continue

        rows = group_by_y(
            [
                {
                    "t": line["t"],
                    "x0": line["cx"],
                    "cx": line["cx"],
                    "cy": line["cy"],
                }
                for line in lines
            ],
            tol=8,
        )

        for row in rows:
            ordered = sorted(row, key=lambda item: item["cx"])
            text = normalize_ocr_text(" ".join(item["t"] for item in ordered))
            if "FUNDA" not in text and "LAJE" not in text and "LAIE" not in text:
                continue
            row_y = sum(item["cy"] for item in ordered) / len(ordered)
            candidate_rows.append((row_y, text))

    if not candidate_rows:
        return []

    candidate_rows.sort(key=lambda item: item[0])
    clustered: list[dict] = []
    for row_y, text in candidate_rows:
        for cluster in clustered:
            if abs(cluster["y"] - row_y) <= OCR_LEVEL_ROW_TOL_Y:
                cluster["ys"].append(row_y)
                cluster["texts"].append(text)
                cluster["y"] = sum(cluster["ys"]) / len(cluster["ys"])
                break
        else:
            clustered.append({"y": row_y, "ys": [row_y], "texts": [text]})

    clustered.sort(key=lambda item: item["y"])
    fund_rows = [cluster for cluster in clustered if any("FUNDA" in text for text in cluster["texts"])]
    laje_rows = [cluster for cluster in clustered if cluster not in fund_rows]
    if not laje_rows:
        return []

    levels: list[tuple[str, float]] = []
    laje_count = len(laje_rows)
    for index, cluster in enumerate(laje_rows):
        explicit = None
        for text in cluster["texts"]:
            match = RE_LEVEL_DIGIT.search(text)
            if match:
                explicit = int(match.group(1))
                break
        floor_number = explicit if explicit is not None else laje_count - index
        levels.append((f"{floor_number}A LAJE", cluster["y"]))

    if fund_rows:
        levels.append(("FUNDACAO", fund_rows[0]["y"]))

    return levels


def attach_named_level_entries(page, boxes: list[dict]) -> bool:
    named_levels = detect_named_levels(page, boxes)
    if len(named_levels) < 2:
        return False

    for box in boxes:
        box["levels"] = [{"val": name, "x": box["cx"], "y": y} for name, y in named_levels]
        box["_named_longitudinal_entries"] = []

        for index in range(len(named_levels) - 1):
            level_name, level_y = named_levels[index]
            next_y = named_levels[index + 1][1]
            strip = fitz.Rect(
                min(page.rect.width, box["x1"] + OCR_BAND_STRIP_X_PAD_LEFT),
                max(0.0, level_y + OCR_BAND_STRIP_Y_PAD),
                min(page.rect.width, box["x1"] + OCR_BAND_STRIP_X_PAD_RIGHT),
                min(page.rect.height, next_y - OCR_BAND_STRIP_Y_PAD),
            )
            if strip.x1 - strip.x0 < 20 or strip.y1 - strip.y0 < 20:
                continue

            lines = get_crop_ocr_lines(page, strip, OCR_STRIP_SCALE, rotate_degrees=270)
            texts = [normalize_ocr_text(line["t"]) for line in lines]
            if not texts:
                continue

            direct_entries: list[tuple[int, float]] = []
            c_lengths: list[str] = []
            for text in texts:
                direct_entries.extend(extract_long_matches_from_text(text))
                c_lengths.extend(
                    match
                    for match in RE_OCR_C_LENGTH.findall(text)
                    if int(match) >= 70
                )

            token_entries: list[tuple[int, float]] = []
            for pos, text in enumerate(texts[:-1]):
                qty = parse_ocr_qty_token(text)
                next_text = texts[pos + 1]
                if qty is None:
                    continue
                if next_text.startswith("Φ"):
                    token_matches = extract_long_matches_from_text(f"{text} {next_text}")
                    token_entries.extend(token_matches)

            entries = direct_entries or token_entries
            if not entries:
                continue

            if len(entries) == 1 and len(c_lengths) > 1:
                entries = entries * len(c_lengths)

            for entry_index, (qty, diam) in enumerate(entries, start=1):
                box["_named_longitudinal_entries"].append(
                    (
                        normalize_level_key(level_name),
                        qty,
                        normalize_longitudinal_diameter(diam),
                        f"{normalize_level_key(level_name)}#{entry_index}",
                        True,
                    )
                )

    return any(box.get("_named_longitudinal_entries") for box in boxes)


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

    if box.get("levels") and row_y < min(item["y"] for item in box["levels"]):
        return True

    return any(
        segment["y0"] - REBAR_ROW_TOL_Y <= row_y <= segment["y1"] + REBAR_ROW_TOL_Y
        and segment_crosses_level_line(segment, level)
        for segment in segments
    )


def extract_long_bars(
    spans: list[dict],
    box: dict,
    lance_map: dict[str, int],
    vertical_lines: list[dict] | None = None,
) -> list[tuple[int, int, float, str, bool]]:
    if box.get("_named_longitudinal_entries"):
        results: list[tuple[int, int, float, str, bool]] = []
        for level_name, qty, diam, source, confirmed in box["_named_longitudinal_entries"]:
            level_key = normalize_level_key(level_name)
            if level_key in lance_map:
                results.append((lance_map[level_key], qty, diam, source, confirmed))
        return results

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
    ordered_rows = [sorted(row, key=lambda span: span["x0"]) for row in rows]
    results: list[tuple[int, int, float, str, bool]] = []

    for row_index, ordered in enumerate(ordered_rows):
        next_ordered = ordered_rows[row_index + 1] if row_index + 1 < len(ordered_rows) else []
        next_row_is_close = bool(next_ordered) and abs(next_ordered[0]["cy"] - ordered[0]["cy"]) <= 8
        index = 0
        while index < len(ordered):
            if not RE_PX.match(ordered[index]["t"]):
                index += 1
                continue

            next_index = index + 1
            while next_index < len(ordered):
                if RE_PX.match(ordered[next_index]["t"]):
                    break
                next_index += 1

            token_candidates = list(ordered[index + 1 : next_index])
            if next_row_is_close:
                next_p_x0 = ordered[next_index]["x0"] if next_index < len(ordered) else float("inf")
                token_candidates.extend(
                    span
                    for span in next_ordered
                    if not RE_PX.match(span["t"])
                    and span["x0"] + 1 >= ordered[index]["x0"]
                    and span["x0"] < next_p_x0 - 1
                )
                token_candidates.sort(key=lambda span: (span["x0"], span["cy"]))

            has_pitch_token = any(RE_C_SLASH.match(span["t"]) for span in token_candidates)
            has_length_token = any(RE_OCR_C_LENGTH.search(span["t"]) for span in token_candidates)
            qty: int | None = None
            diam: float | None = None
            for candidate in token_candidates:
                matches = extract_long_matches_from_text(candidate["t"])
                if matches:
                    qty, diam = matches[0]
                    break

                if qty is None and RE_QTY.match(candidate["t"]):
                    qty = int(candidate["t"])
                elif qty is not None:
                    match = RE_PHI.match(candidate["t"])
                    if match:
                        diam = norm(match.group(1))
                        break

            if qty is not None and diam is not None and diam >= BITOLA_MIN_LONG:
                source_token = ordered[index]["t"]
                if has_pitch_token and RE_PX.match(source_token):
                    box.setdefault("_pitch_source_tokens", set()).add(source_token)

                if has_pitch_token and qty > 12:
                    index = next_index if next_index > index else index + 1
                    continue
                if has_length_token and qty > 12 and not has_pitch_token:
                    index = next_index if next_index > index else index + 1
                    continue
                if has_length_token and qty > 12 and diam <= BITOLA_MIN_LONG:
                    index = next_index if next_index > index else index + 1
                    continue
                level = find_level_above_bar(ordered[index]["cy"], box["levels"])
                if level is not None:
                    level_key = normalize_level_key(level["val"])
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


def filter_bar_entries(
    entries: list[tuple[int, int, float, str, bool]],
    excluded_source_tokens: set[str] | None = None,
) -> list[tuple[int, int, float, str, bool]]:
    grouped: dict[tuple[int, float, str], list[tuple[int, int, float, str, bool]]] = defaultdict(list)
    for entry in entries:
        lance, qty, diam, source, confirmed = entry
        source_token = source.split("@", 1)[0]
        if excluded_source_tokens and source_token in excluded_source_tokens and qty > 12 and not confirmed:
            continue
        grouped[(lance, diam, source_token)].append(entry)

    filtered: list[tuple[int, int, float, str, bool]] = []
    for group in grouped.values():
        if len(group) > 1 and any(entry[4] for entry in group):
            filtered.extend(entry for entry in group if entry[4])
        else:
            filtered.extend(group)

    return filtered


def source_y(entry: tuple[int, int, float, str, bool]) -> float:
    source = entry[3]
    if "@" not in source:
        return float("inf")
    try:
        return float(source.rsplit("@", 1)[1])
    except ValueError:
        return float("inf")


def keep_top_cluster_if_single_lance(
    entries: list[tuple[int, int, float, str, bool]],
    cluster_tol: float = 35.0,
) -> list[tuple[int, int, float, str, bool]]:
    if len({entry[0] for entry in entries}) != 1:
        return entries
    if len(entries) <= 1:
        return entries

    top_y = min(source_y(entry) for entry in entries)
    if not math.isfinite(top_y):
        return entries

    filtered = [entry for entry in entries if source_y(entry) <= top_y + cluster_tol]
    return filtered or entries


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
    if not boxes:
        ocr_spans = get_ocr_spans(page)
        if ocr_spans:
            spans.extend(ocr_spans)
            boxes = find_boxes(spans)
    assign_levels(spans, boxes)
    refine_box_bounds_by_level_rows(boxes)
    assign_levels(spans, boxes)
    fill_missing_consensus_levels(boxes)
    if not collect_unique_levels(boxes):
        attach_named_level_entries(page, boxes)
    attach_level_division_lines(boxes, horizontal_lines)
    doc.close()

    print(f"Boxes identificados: {len(boxes)}")

    if discover:
        print("\n=== DISCOVER MODE ===")
        for box in boxes:
            box_levels = [(format_level(level["val"]), round(level["y"], 2)) for level in box["levels"]]
            origin = "OCR" if box.get("ocr") else "PDF"
            print(f"\n  {box['raw']!r:40s} -> {box['names']} [{origin}]")
            print(f"    Niveis (valor, y-PDF): {box_levels}")

    levels = collect_unique_levels(boxes)
    if not levels:
        if boxes and discover:
            print("\nNenhum nivel foi encontrado no PDF.")
            return

        if boxes:
            names = ", ".join(dict.fromkeys(name for box in boxes for name in box["names"]))
            sys.exit(f"[ERRO] Pilares reconhecidos ({names}), mas nenhum nivel foi encontrado no PDF.")
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

    known_lances = collect_known_lances_for_boxes(boxes)
    if not known_lances:
        known_lances = read_known_lances_from_env()

    default_map = build_default_lance_map(assignable_levels, known_lances=known_lances)

    if discover:
        print("\n=== NIVEIS UNICOS ===")
        for level in assignable_levels:
            suggestion = default_map.get(normalize_level_key(level))
            extra = f" -> sugestao de lance {suggestion}" if suggestion is not None else ""
            print(f"  {format_level(level)}{extra}")

        print("\nRode sem --discover para confirmar o mapeamento e gerar o CSV.")
        return

    automation_mode = bool(os.environ.get("ARMPIL_RESULT_FILE", "").strip())

    if not assignable_levels:
        lance_map = {}
        print("Nenhum trecho de lance com armadura longitudinal foi identificado.")
    elif has_complete_lance_map(assignable_levels, default_map):
        lance_map = {normalize_level_key(level): default_map[normalize_level_key(level)] for level in assignable_levels}
        print("Mapeamento de lances aplicado automaticamente.")
    elif automation_mode:
        lance_map = default_map
        mapped_levels = ", ".join(
            format_level(level) for level in assignable_levels if normalize_level_key(level) in lance_map
        )
        skipped_levels = ", ".join(
            format_level(level) for level in assignable_levels if normalize_level_key(level) not in lance_map
        )
        if mapped_levels:
            print(f"Mapeamento parcial aplicado: {mapped_levels}")
        if skipped_levels:
            print(f"Niveis ignorados: {skipped_levels}")
    else:
        lance_map = request_lance_map(assignable_levels)

    raw_rows: dict[tuple[str, int], list[tuple[int, float, str]]] = defaultdict(list)
    for box in boxes:
        data = extract_long_bars(spans, box, lance_map, vertical_lines)
        data = filter_bar_entries(data, box.get("_pitch_source_tokens"))
        data = keep_top_cluster_if_single_lance(data)
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
            all_rows.append((pilar, lance, qty, fmt_num(diam), f"{calc_as(qty, diam):.10g}"))

    if out_csv is None:
        sys.exit("[ERRO] Caminho de saida do CSV nao definido.")

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(["Pilar", "Lance", "Qtd (Qf)", "Bitola (mm)", "As Total (cm2)"])
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
