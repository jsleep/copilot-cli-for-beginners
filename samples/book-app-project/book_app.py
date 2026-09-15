import sys
from books import BookCollection


# Global collection instance
collection = BookCollection()


def show_books(books):
    """Display books in a user-friendly format."""
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")

    for index, book in enumerate(books, start=1):
        status = "✓" if book.read else " "
        print(f"{index}. [{status}] {book.title} by {book.author} ({book.year})")

    print()


def handle_list():
    books = collection.list_books()
    show_books(books)


def handle_list_unread() -> None:
    books = collection.get_unread_books()
    show_books(books)


def handle_add():
    print("\nAdd a New Book\n")

    title = input("Title: ").strip()
    author = input("Author: ").strip()
    year_str = input("Year: ").strip()

    try:
        year = int(year_str) if year_str else 0
        collection.add_book(title, author, year)
        print("\nBook added successfully.\n")
    except ValueError as e:
        print(f"\nError: {e}\n")


def handle_remove():
    print("\nRemove a Book\n")

    title = input("Enter the title of the book to remove: ").strip()
    collection.remove_book(title)

    print("\nBook removed if it existed.\n")


def handle_find():
    print("\nFind Books by Author\n")

    author = input("Author name: ").strip()
    books = collection.find_by_author(author)

    show_books(books)


def handle_search_year() -> None:
    print("\nFind Books by Publication Year\n")

    start_year_input = input("Start year: ").strip()
    end_year_input = input("End year: ").strip()

    try:
        start_year = int(start_year_input)
        end_year = int(end_year_input)
    except ValueError:
        print("\nError: Years must be whole numbers.\n")
        return

    try:
        books = collection.find_by_year_range(start_year, end_year)
    except ValueError as error:
        print(f"\nError: {error}\n")
        return

    show_books(books)


def show_help():
    print("""
Book Collection Helper

Commands:
  list         - Show all books
  list unread  - Show unread books
  add          - Add a new book
  remove       - Remove a book by title
  find         - Find books by author
  find-year    - Find books published between two years
  help         - Show this help message
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "list" and len(sys.argv) > 2 and sys.argv[2].lower() == "unread":
        handle_list_unread()
    elif command == "list":
        handle_list()
    elif command == "add":
        handle_add()
    elif command == "remove":
        handle_remove()
    elif command == "find":
        handle_find()
    elif command == "find-year":
        handle_search_year()
    elif command == "help":
        show_help()
    else:
        print("Unknown command.\n")
        show_help()


if __name__ == "__main__":
    main()
