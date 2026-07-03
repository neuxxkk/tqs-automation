from __future__ import annotations

from armpil_extractor import (
    assign_levels,
    build_default_lance_map,
    extract_long_matches_from_text,
    extract_long_bars,
    fill_missing_consensus_levels,
    get_default_lance_for_level,
    get_first_positive_lance,
    keep_contiguous_level_sequence,
    keep_dominant_level_x_cluster,
    keep_top_cluster_if_single_lance,
    parse_names,
    pillar_sort_key,
    shift_lance_map_start,
)


def test_get_default_lance_for_level_accepts_numeric_strings() -> None:
    assert get_default_lance_for_level("1040.25") == 0
    assert get_default_lance_for_level("1043.40") == 6
    assert get_default_lance_for_level("1046.60") == 7


def test_build_default_lance_map_handles_string_levels_from_pdf_117() -> None:
    levels = ["1040.25", "1043.40", "1046.60"]

    assert build_default_lance_map(levels) == {
        "1040.25": 0,
        "1043.40": 6,
        "1046.60": 7,
    }


def test_build_default_lance_map_handles_pdf_177_levels() -> None:
    levels = ["1046.60", "1050.35", "1050.95", "1051.00"]

    assert build_default_lance_map(levels) == {
        "1046.60": 7,
        "1050.35": 8,
        "1050.95": 8,
        "1051.00": 8,
    }


def test_build_default_lance_map_handles_pdf_220_levels() -> None:
    levels = ["1055.91", "1059.11", "1062.31", "1065.51", "1068.71", "1071.91"]

    assert build_default_lance_map(levels) == {
        "1055.91": 10,
        "1059.11": 11,
        "1062.31": 12,
        "1065.51": 13,
        "1068.71": 14,
        "1071.91": 15,
    }


def test_build_default_lance_map_prefers_complete_historical_defaults_over_known_lances(monkeypatch) -> None:
    monkeypatch.setenv("ARMPIL_KNOWN_LANCES", "29,30,31,32,33,34")
    levels = ["1055.91", "1059.11", "1062.31", "1065.51", "1068.71", "1071.91"]

    assert build_default_lance_map(levels) == {
        "1055.91": 10,
        "1059.11": 11,
        "1062.31": 12,
        "1065.51": 13,
        "1068.71": 14,
        "1071.91": 15,
    }


def test_shift_lance_map_start_preserves_relative_spacing() -> None:
    levels = ["1050.95", "1055.91", "1059.11", "1062.31"]
    mapping = {
        "1050.95": 0,
        "1055.91": 29,
        "1059.11": 30,
        "1062.31": 31,
    }

    assert get_first_positive_lance(levels, mapping) == 29
    assert shift_lance_map_start(levels, mapping, 23) == {
        "1050.95": 0,
        "1055.91": 23,
        "1059.11": 24,
        "1062.31": 25,
    }


def test_keep_top_cluster_if_single_lance_keeps_upper_group() -> None:
    entries = [
        (8, 54, 16.0, "P1@331.2", True),
        (8, 10, 16.0, "P2@353.6", True),
        (8, 24, 16.0, "P1@835.2", False),
    ]

    assert keep_top_cluster_if_single_lance(entries) == entries[:2]


def test_assign_levels_extends_contiguous_sequence_below_initial_window() -> None:
    box = {"cy": 76.77, "cx": 202.72, "x_left": 43.69, "x_right": 361.74}
    spans = [
        {"t": "+1071,91", "cx": 145.98, "cy": 100.83, "sz": 11.66, "ang": 0.0},
        {"t": "+1068,71", "cx": 145.98, "cy": 327.36, "sz": 11.66, "ang": 0.0},
        {"t": "+1065,51", "cx": 145.98, "cy": 553.90, "sz": 11.66, "ang": 0.0},
        {"t": "+1062,31", "cx": 145.98, "cy": 780.44, "sz": 11.66, "ang": 0.0},
        {"t": "+1059,11", "cx": 145.98, "cy": 1006.97, "sz": 11.66, "ang": 0.0},
        {"t": "+1055,91", "cx": 145.98, "cy": 1233.51, "sz": 11.66, "ang": 0.0},
        {"t": "+1050,95", "cx": 145.98, "cy": 1584.64, "sz": 11.66, "ang": 0.0},
    ]

    assign_levels(spans, [box])

    assert [round(level["val"], 2) for level in box["levels"]] == [
        1050.95,
        1055.91,
        1059.11,
        1062.31,
        1065.51,
        1068.71,
        1071.91,
    ]


def test_fill_missing_consensus_levels_restores_shared_top_level() -> None:
    boxes = [
        {
            "cx": 100.0,
            "levels": [
                {"val": 1055.91, "x": 90.0, "y": 1200.0},
                {"val": 1059.11, "x": 90.0, "y": 980.0},
                {"val": 1062.31, "x": 90.0, "y": 760.0},
                {"val": 1065.51, "x": 90.0, "y": 540.0},
                {"val": 1068.71, "x": 90.0, "y": 320.0},
                {"val": 1071.91, "x": 90.0, "y": 100.0},
            ],
        },
        {
            "cx": 200.0,
            "levels": [
                {"val": 1055.91, "x": 190.0, "y": 1201.0},
                {"val": 1059.11, "x": 190.0, "y": 981.0},
                {"val": 1062.31, "x": 190.0, "y": 761.0},
                {"val": 1065.51, "x": 190.0, "y": 541.0},
                {"val": 1068.71, "x": 190.0, "y": 321.0},
            ],
        },
        {
            "cx": 300.0,
            "levels": [
                {"val": 1055.91, "x": 290.0, "y": 1199.0},
                {"val": 1059.11, "x": 290.0, "y": 979.0},
                {"val": 1062.31, "x": 290.0, "y": 759.0},
                {"val": 1065.51, "x": 290.0, "y": 539.0},
                {"val": 1068.71, "x": 290.0, "y": 319.0},
                {"val": 1071.91, "x": 290.0, "y": 99.0},
            ],
        },
    ]

    fill_missing_consensus_levels(boxes)

    assert [round(level["val"], 2) for level in boxes[1]["levels"]] == [
        1055.91,
        1059.11,
        1062.31,
        1065.51,
        1068.71,
        1071.91,
    ]


def test_extract_long_bars_skips_large_c_length_rows_without_pitch_token() -> None:
    spans = [
        {"t": "P1", "x0": 10.0, "x1": 20.0, "cx": 15.0, "cy": 120.0, "sz": 11.1, "ang": 0.0},
        {"t": "22", "x0": 25.0, "x1": 35.0, "cx": 30.0, "cy": 120.0, "sz": 8.6, "ang": 0.0},
        {"t": "O 25", "x0": 40.0, "x1": 60.0, "cx": 50.0, "cy": 120.0, "sz": 8.6, "ang": 0.0},
        {"t": "P2", "x0": 10.0, "x1": 20.0, "cx": 15.0, "cy": 160.0, "sz": 11.1, "ang": 0.0},
        {"t": "49", "x0": 25.0, "x1": 35.0, "cx": 30.0, "cy": 160.0, "sz": 8.6, "ang": 0.0},
        {"t": "O 12.5", "x0": 40.0, "x1": 65.0, "cx": 52.5, "cy": 160.0, "sz": 8.6, "ang": 0.0},
        {"t": "C=316", "x0": 70.0, "x1": 95.0, "cx": 82.5, "cy": 160.0, "sz": 8.6, "ang": 0.0},
    ]
    box = {
        "x_left": 0.0,
        "x_right": 100.0,
        "cy": 0.0,
        "levels": [
            {"val": 1055.91, "x": 5.0, "y": 200.0},
            {"val": 1071.91, "x": 5.0, "y": 80.0},
        ],
    }

    assert extract_long_bars(spans, box, {"1055.91": 10, "1071.91": 15}) == [
        (15, 22, 25.0, "P1@120.0", True),
    ]


def test_keep_contiguous_level_sequence_stops_when_neighbor_column_reverses_value_order() -> None:
    levels = [
        {"val": 1054.33, "x": 152.8, "y": 717.1},
        {"val": 1050.35, "x": 152.8, "y": 998.8},
        {"val": 1055.60, "x": 150.5, "y": 1178.1},
        {"val": 1050.35, "x": 150.5, "y": 1549.8},
    ]

    assert [round(level["val"], 2) for level in keep_contiguous_level_sequence(levels)] == [
        1054.33,
        1050.35,
    ]


def test_keep_dominant_level_x_cluster_prefers_column_that_starts_near_title() -> None:
    levels = [
        {"val": 1054.33, "x": 1226.9, "y": 169.9},
        {"val": 1050.60, "x": 1226.9, "y": 434.0},
        {"val": 1055.60, "x": 1276.5, "y": 627.2},
        {"val": 1054.33, "x": 1283.5, "y": 717.1},
        {"val": 1050.35, "x": 1276.5, "y": 998.9},
    ]

    selected = keep_dominant_level_x_cluster(levels, box_cx=1200.0, box_cy=145.8)

    assert [(round(level["val"], 2), round(level["y"], 1)) for level in selected] == [
        (1054.33, 169.9),
        (1050.6, 434.0),
    ]


def test_extract_long_matches_from_text_handles_compact_vector_tokens() -> None:
    assert extract_long_matches_from_text("8 Ø 12.5") == [(8, 12.5)]


def test_parse_names_accepts_any_prefix_starting_with_p() -> None:
    assert parse_names("P21=PMA21=PP21=PAF21") == ["P21", "PMA21", "PP21", "PAF21"]


def test_pillar_sort_key_handles_extended_prefixes() -> None:
    ordered = sorted(["PMA21", "P21", "PP21", "PAF21"], key=pillar_sort_key)

    assert ordered == ["P21", "PAF21", "PMA21", "PP21"]
