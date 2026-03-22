"""Tests for tree view rendering."""

from docmost_cli.output.tree import print_tree


class TestPrintTree:
    def test_nested_pages(self, capsys) -> None:
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
        print_tree(pages)
        output = capsys.readouterr().out
        assert "Parent Page" in output
        assert "Child Page" in output
        assert "Grandchild" in output
        assert "Second Child" in output

    def test_empty_list(self, capsys) -> None:
        print_tree([])
        output = capsys.readouterr().out
        assert output == ""

    def test_multiple_root_pages(self, capsys) -> None:
        pages = [
            {"id": "r1", "title": "First Root", "children": []},
            {"id": "r2", "title": "Second Root", "children": []},
        ]
        print_tree(pages)
        output = capsys.readouterr().out
        assert "First Root" in output
        assert "Second Root" in output

    def test_page_with_icon(self, capsys) -> None:
        pages = [
            {"id": "p1", "title": "Docs", "icon": "book", "children": []},
        ]
        print_tree(pages)
        output = capsys.readouterr().out
        assert "book" in output
        assert "Docs" in output
