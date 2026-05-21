from __future__ import annotations

from armpil_extractor import (
    build_default_lance_map,
    get_default_lance_for_level,
    keep_top_cluster_if_single_lance,
    parse_names,
    pillar_sort_key,
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


def test_keep_top_cluster_if_single_lance_keeps_upper_group() -> None:
    entries = [
        (8, 54, 16.0, "P1@331.2", True),
        (8, 10, 16.0, "P2@353.6", True),
        (8, 24, 16.0, "P1@835.2", False),
    ]

    assert keep_top_cluster_if_single_lance(entries) == entries[:2]


def test_parse_names_accepts_any_prefix_starting_with_p() -> None:
    assert parse_names("P21=PMA21=PP21=PAF21") == ["P21", "PMA21", "PP21", "PAF21"]


def test_pillar_sort_key_handles_extended_prefixes() -> None:
    ordered = sorted(["PMA21", "P21", "PP21", "PAF21"], key=pillar_sort_key)

    assert ordered == ["P21", "PAF21", "PMA21", "PP21"]
