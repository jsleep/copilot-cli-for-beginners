import sys
import os
from types import ModuleType
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def mixed_collection() -> BookCollection:
    """Provide a collection containing read and unread books."""
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    collection.mark_as_read("1984")
    return collection


@pytest.fixture
def book_app_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Provide the CLI module with an isolated collection."""
    import book_app

    monkeypatch.setattr(book_app, "collection", BookCollection())
    return book_app


def test_add_book():
    collection = BookCollection()
    initial_count = len(collection.books)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.books) == initial_count + 1
    book = collection.find_book_by_title("1984")
    assert book is not None
    assert book.author == "George Orwell"
    assert book.year == 1949
    assert book.read is False

def test_mark_book_as_read():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    result = collection.mark_as_read("Dune")
    assert result is True
    book = collection.find_book_by_title("Dune")
    assert book.read is True

def test_mark_book_as_read_invalid():
    collection = BookCollection()
    result = collection.mark_as_read("Nonexistent Book")
    assert result is False

def test_remove_book():
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    result = collection.remove_book("The Hobbit")
    assert result is True
    book = collection.find_book_by_title("The Hobbit")
    assert book is None

def test_remove_book_invalid():
    collection = BookCollection()
    result = collection.remove_book("Nonexistent Book")
    assert result is False


class TestGetUnreadBooks:
    """Tests for BookCollection.get_unread_books."""

    def test_mixed_collection_returns_only_unread_books(
        self, mixed_collection: BookCollection
    ) -> None:
        unread_books = mixed_collection.get_unread_books()

        assert [book.title for book in unread_books] == ["Dune", "The Hobbit"]

    def test_empty_collection_returns_empty_list(self) -> None:
        collection = BookCollection()

        unread_books = collection.get_unread_books()

        assert unread_books == []

    def test_all_books_read_returns_empty_list(self) -> None:
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.mark_as_read("Dune")

        unread_books = collection.get_unread_books()

        assert unread_books == []

    def test_no_books_read_returns_all_books_in_original_order(self) -> None:
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("1984", "George Orwell", 1949)

        unread_books = collection.get_unread_books()

        assert [book.title for book in unread_books] == ["Dune", "1984"]

    def test_filtering_does_not_modify_collection(
        self, mixed_collection: BookCollection
    ) -> None:
        mixed_collection.get_unread_books()

        assert len(mixed_collection.list_books()) == 3

    def test_marking_book_as_read_removes_it_from_results(
        self, mixed_collection: BookCollection
    ) -> None:
        mixed_collection.mark_as_read("Dune")

        unread_books = mixed_collection.get_unread_books()

        assert [book.title for book in unread_books] == ["The Hobbit"]

    def test_removing_unread_book_removes_it_from_results(
        self, mixed_collection: BookCollection
    ) -> None:
        mixed_collection.remove_book("Dune")

        unread_books = mixed_collection.get_unread_books()

        assert [book.title for book in unread_books] == ["The Hobbit"]

    def test_filtering_uses_read_status_loaded_from_file(
        self, mixed_collection: BookCollection
    ) -> None:
        reloaded_collection = BookCollection()

        unread_books = reloaded_collection.get_unread_books()

        assert [book.title for book in unread_books] == ["Dune", "The Hobbit"]


class TestListUnreadCommand:
    """Tests for the list unread CLI command."""

    def test_handler_displays_only_unread_books(
        self,
        book_app_module: ModuleType,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_app_module.collection.add_book("Dune", "Frank Herbert", 1965)
        book_app_module.collection.add_book("1984", "George Orwell", 1949)
        book_app_module.collection.mark_as_read("1984")

        book_app_module.handle_list_unread()

        output = capsys.readouterr().out
        assert "Dune" in output and "1984" not in output

    def test_handler_displays_empty_message_when_no_books_are_unread(
        self,
        book_app_module: ModuleType,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_app_module.handle_list_unread()

        output = capsys.readouterr().out

        assert output == "No books found.\n"

    def test_main_routes_list_unread_to_handler(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        handler = Mock()
        monkeypatch.setattr(sys, "argv", ["book_app.py", "list", "unread"])
        monkeypatch.setattr(book_app_module, "handle_list_unread", handler)

        book_app_module.main()

        handler.assert_called_once_with()

    def test_main_accepts_case_insensitive_list_unread(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        handler = Mock()
        monkeypatch.setattr(sys, "argv", ["book_app.py", "LIST", "UNREAD"])
        monkeypatch.setattr(book_app_module, "handle_list_unread", handler)

        book_app_module.main()

        handler.assert_called_once_with()

    def test_help_documents_list_unread(
        self,
        book_app_module: ModuleType,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_app_module.show_help()

        output = capsys.readouterr().out

        assert "list unread  - Show unread books" in output


class TestFindByYearRange:
    """Tests for BookCollection.find_by_year_range."""

    @pytest.mark.parametrize(
        "start_year,end_year,expected_titles",
        [
            (1937, 1949, ["1984", "The Hobbit"]),
            (1965, 1965, ["Dune"]),
            (1937, 1965, ["Dune", "1984", "The Hobbit"]),
        ],
    )
    def test_returns_books_within_inclusive_range(
        self,
        mixed_collection: BookCollection,
        start_year: int,
        end_year: int,
        expected_titles: list[str],
    ) -> None:
        books_in_range = mixed_collection.find_by_year_range(start_year, end_year)

        assert [book.title for book in books_in_range] == expected_titles

    @pytest.mark.parametrize(
        "start_year,end_year",
        [
            (2000, 2020),
            (1900, 1936),
            (1966, 2000),
        ],
    )
    def test_returns_empty_list_when_no_books_match(
        self,
        mixed_collection: BookCollection,
        start_year: int,
        end_year: int,
    ) -> None:
        books_in_range = mixed_collection.find_by_year_range(start_year, end_year)

        assert books_in_range == []

    def test_empty_collection_returns_empty_list(self) -> None:
        collection = BookCollection()

        books_in_range = collection.find_by_year_range(1900, 2000)

        assert books_in_range == []

    def test_preserves_order_without_modifying_collection(
        self, mixed_collection: BookCollection
    ) -> None:
        books_in_range = mixed_collection.find_by_year_range(1900, 2000)

        assert [book.title for book in books_in_range] == [
            "Dune",
            "1984",
            "The Hobbit",
        ]
        assert [book.title for book in mixed_collection.list_books()] == [
            "Dune",
            "1984",
            "The Hobbit",
        ]

    @pytest.mark.parametrize(
        "start_year,end_year",
        [
            (2000, 1900),
            (1965, 1964),
            (1, 0),
        ],
    )
    def test_rejects_reversed_range(
        self,
        mixed_collection: BookCollection,
        start_year: int,
        end_year: int,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Start year must be less than or equal to end year",
        ):
            mixed_collection.find_by_year_range(start_year, end_year)

    @pytest.mark.parametrize(
        "start_year,end_year",
        [
            ("1937", 1965),
            (1937, "1965"),
            (None, 1965),
            (1937, None),
            (1937.0, 1965),
            (1937, 1965.0),
            (True, 1965),
            (1937, False),
        ],
    )
    def test_rejects_non_integer_years(
        self,
        mixed_collection: BookCollection,
        start_year: object,
        end_year: object,
    ) -> None:
        with pytest.raises(
            ValueError,
            match="Start year and end year must be integers",
        ):
            mixed_collection.find_by_year_range(start_year, end_year)


class TestFindYearCommand:
    """Tests for the find-year CLI command."""

    def test_handler_displays_matching_books(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_app_module.collection.add_book("Dune", "Frank Herbert", 1965)
        book_app_module.collection.add_book("1984", "George Orwell", 1949)
        monkeypatch.setattr("builtins.input", Mock(side_effect=["1940", "1950"]))

        book_app_module.handle_search_year()

        output = capsys.readouterr().out
        assert "1984" in output and "Dune" not in output

    def test_handler_displays_empty_message_when_no_books_match(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("builtins.input", Mock(side_effect=["2000", "2020"]))

        book_app_module.handle_search_year()

        output = capsys.readouterr().out
        assert output.endswith("No books found.\n")

    def test_handler_rejects_non_numeric_year(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("builtins.input", Mock(side_effect=["old", "2020"]))

        book_app_module.handle_search_year()

        output = capsys.readouterr().out
        assert "Error: Years must be whole numbers." in output

    def test_handler_rejects_reversed_range(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("builtins.input", Mock(side_effect=["2020", "2000"]))

        book_app_module.handle_search_year()

        output = capsys.readouterr().out
        assert "Start year must be less than or equal to end year." in output

    def test_main_routes_find_year_to_handler(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        handler = Mock()
        monkeypatch.setattr(sys, "argv", ["book_app.py", "find-year"])
        monkeypatch.setattr(book_app_module, "handle_search_year", handler)

        book_app_module.main()

        handler.assert_called_once_with()

    def test_main_accepts_case_insensitive_find_year(
        self,
        book_app_module: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        handler = Mock()
        monkeypatch.setattr(sys, "argv", ["book_app.py", "FIND-YEAR"])
        monkeypatch.setattr(book_app_module, "handle_search_year", handler)

        book_app_module.main()

        handler.assert_called_once_with()

    def test_help_documents_find_year(
        self,
        book_app_module: ModuleType,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        book_app_module.show_help()

        output = capsys.readouterr().out
        assert "find-year    - Find books published between two years" in output
