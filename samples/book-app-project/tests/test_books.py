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
