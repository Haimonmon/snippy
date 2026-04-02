"""
## Snippy
Snippy is a book scraper that helps you `scrape`, books online.

Snippy is a personal librarian assistant,
it quietly explores the web, finds books,  
and brings them back to your digital shelf.

--------------------------------------------
` Package By: 🧙‍♂️ Haimonmon `
"""

from .main import seek_checkup, seek_openlibrary, seek_openlibrary_links, seek_openlibrary_book, seek_barnesnobles, seek_barnesnobles_book_list, seek_barnesnobles_book, reset_openlibrary

__all__ = [
    "seek_checkup", 
    "seek_openlibrary", "seek_openlibrary_links", "seek_openlibrary_book", "reset_openlibrary",
    "seek_barnesnobles", "seek_barnesnobles_book_list", "seek_barnesnobles_book"
]