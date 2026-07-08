import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from src.finder_sight.core.duplicate_finder import (
    find_duplicate_groups,
    plan_duplicate_deletions,
    sort_group_by_quality,
)


def test_find_duplicate_groups_from_added_directories(tmp_path):
    library = tmp_path / "library"
    outside = tmp_path / "outside"
    library.mkdir()
    outside.mkdir()

    first = library / "a.jpg"
    second = library / "b.jpg"
    third = library / "c.jpg"
    ignored = outside / "ignored.jpg"
    for path in (first, second, third, ignored):
        path.write_bytes(b"image")

    groups = find_duplicate_groups(
        {
            str(first): "same-hash",
            str(second): "same-hash",
            str(third): "unique-hash",
            str(ignored): "same-hash",
        },
        [str(library)],
    )

    assert groups == [[str(first), str(second)]]


def test_find_duplicate_groups_ignores_missing_files(tmp_path):
    first = tmp_path / "a.jpg"
    first.write_bytes(b"image")
    missing = tmp_path / "missing.jpg"

    groups = find_duplicate_groups(
        {
            str(first): "same-hash",
            str(missing): "same-hash",
        }
    )

    assert groups == []


def test_sort_group_by_quality_prefers_higher_resolution(tmp_path):
    small = tmp_path / "small.jpg"
    large = tmp_path / "large.jpg"
    Image.new("RGB", (100, 100), color="red").save(small)
    Image.new("RGB", (300, 300), color="red").save(large)

    ranked = sort_group_by_quality([str(small), str(large)])

    assert ranked[0] == str(large)


def test_plan_duplicate_deletions_keeps_best_quality(tmp_path):
    small = tmp_path / "small.jpg"
    large = tmp_path / "large.jpg"
    Image.new("RGB", (100, 100), color="red").save(small)
    Image.new("RGB", (300, 300), color="red").save(large)

    delete_paths, keepers = plan_duplicate_deletions([[str(small), str(large)]])

    assert delete_paths == [str(small)]
    assert list(keepers) == [str(large)]
