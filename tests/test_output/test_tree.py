"""Tests for tree view rendering."""

import io
import sys

from docmost_cli.output.tree import print_tree


class TestPrintTree:
    def test_nested_pages(self) -> None:
        pages = [
            {
                "id": "p1",
                "title": "Parent Page",
                "icon": "",
                "children": [
                    {
                        "id": "p2",
                        "title": "Child Page",
                        "icon": "",
                        "children": [
                            {
                                "id": "p3",
                                "title": "Grandchild",
                                "icon": "",
                                "children": [],
                            }
                        ],
                    },
                    {
                        "id": "p4",
                        "title": "Second Child",
                        "icon": "",
                        "children": [],
                    },
                ],
            },
        ]
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_tree(pages)
        finally:
            sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "Parent Page" in output
        assert "Child Page" in output
        assert "Grandchild" in output
        assert "Second Child" in output

    def test_empty_list(self) -> None:
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_tree([])
        finally:
            sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert output == ""

    def test_multiple_root_pages(self) -> None:
        pages = [
            {"id": "r1", "title": "First Root", "children": []},
            {"id": "r2", "title": "Second Root", "children": []},
        ]
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_tree(pages)
        finally:
            sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "First Root" in output
        assert "Second Root" in output

    def test_page_with_icon(self) -> None:
        pages = [
            {"id": "p1", "title": "Docs", "icon": "book", "children": []},
        ]
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_tree(pages)
        finally:
            sys.stdout = sys.__stdout__
        output = captured.getvalue()
        assert "book" in output
        assert "Docs" in output
