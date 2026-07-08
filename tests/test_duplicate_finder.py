import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.finder_sight.core.duplicate_finder import find_duplicate_groups


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
