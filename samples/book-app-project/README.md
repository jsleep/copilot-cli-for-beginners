# Book Collection App

*(This README is intentionally rough so you can improve it with GitHub Copilot CLI)*

A Python app for managing books you have or want to read.
It can add, remove, and list books, including showing only unread books.
It can also mark books as read and find books published between two years.

---

## Current Features

* Reads books from a JSON file (our database)
* Finds books published within a range of years
* Input checking is weak in some areas
* Some tests exist but probably not enough

---

## Files

* `book_app.py` - Main CLI entry point
* `books.py` - BookCollection class with data logic
* `utils.py` - Helper functions for UI and input
* `data.json` - Sample book data
* `tests/test_books.py` - Starter pytest tests

---

## Running the App

```bash
python book_app.py list
python book_app.py list unread
python book_app.py add
python book_app.py find
python book_app.py find-year
python book_app.py remove
python book_app.py help
```

## Searching by Publication Year

Use the `find-year` command to find books published between two years:

```bash
python book_app.py find-year
```

The app will ask for the start and end of the range:

```text
Start year: 1930
End year: 1970
```

Both years are included. For example, a search from `1930` through `1970`
includes books published in 1930 and 1970. If no books match, the app displays
`No books found.` If the years are not whole numbers, or the start year is
later than the end year, the app displays an error.

## Running Tests

```bash
python -m pytest tests/
```

---

## Notes

* Not production-ready (obviously)
* Some code could be improved
* Could add more commands later
