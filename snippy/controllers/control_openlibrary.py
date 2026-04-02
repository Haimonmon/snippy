import time
import asyncio

from typing import Dict, Final

from ..file import FileManager
from ..scrapers import OpenLibrary

CLOSED_BOOK_LINKS_FIELD: Final[Dict] = {
    "name": "Open Library InActive Book List",
    "description": "Contains inactive cached library links that contains no any results when open",
    "date_updated": "",
    "main_source": "https://openlibrary.org/",
    "total_inactive_book_links": 0,
    "book_links": []
}

OPEN_BOOK_LINKS_FIELD: Final[Dict] = {
    "name": "Open Library Active Book List",
    "description": "Contains active cached library book links that contains alot of results when open",
    "date_updated": "",
    "main_source": "https://openlibrary.org/",
    "total_active_book_links": 0,
    "book_links": []
}

OPEN_SUBJECT_LINKS_FIELD: Final[Dict] = {
    "name": "Open Library Book Subjects Link List",
    "description": "Contains book links scraped of snippy",
    "date_updated": "",
    "main_source": "https://openlibrary.org/subject/",
    "total_book_links": 0,
    "books": []
}

SHELF_AUTHOR_FIELD: Final[Dict] = {
    "data_title": "Author Data Sets",
    "total_authors": 0,
    "authors": []
}

SHELF_BOOK_FIELD: Final[Dict] = {
    "data_title": "book Data Sets",
    "total_books": 0,
    "books": []
}

SHELF_CATEGORIES_FIELD: Final[Dict] = {
    "data_title": "categorie Data Sets",
    "total_categories": 0,
    "categories": []
}

SHELF_PUBLISHER_FIELD: Final[Dict] = {
    "data_title": "publisher Data Sets",
    "total_publishers": 0,
    "publishers": []
}

SHELF_FIELD: Final[Dict] = {
    "name": "Barnes and Nobles Book List",
    "description": "Contais book meta datas",
    "date_updated": "",
    "main_source": "https://openlibrary.org/",
    "total_books": 0,
    "books": []
}

OPEN_BOOK_PATH: Final[str] = "snippy/cache/openlibrary/open_links/openlibrary_book_links.json"
CLOSED_BOOK_PATH: Final[str] = "snippy/cache/openlibrary/closed_links/openlibrary_book_links.json"
OPEN_SUBJECT_PATH: Final[str]  = "snippy/cache/openlibrary/open_links/openlibrary_subject_links.json"

SHELF_PATH: Final[str] = "snippy/data/openlibrary_shelf/shelf.json"
SHELF_BOOK_PATH: Final[str] = "snippy/data/openlibrary_shelf/book.json"
SHELF_AUTHOR_PATH: Final[str] = "snippy/data/openlibrary_shelf/author.json"
SHELF_PUBLISHER_PATH: Final[str] = "snippy/data/openlibrary_shelf/publisher.json"
SHELF_CATEGORIES_PATH: Final[str] = "snippy/data/openlibrary_shelf/categories.json"

class OpenLibraryController:
    """ Control center for Snippy's ocean of pdf safety checks. """
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.target = OpenLibrary(self.file_manager)

    # def validate_openlibrary(self, agent: Dict[str, str | Dict[str, str]], headless: bool = True, total_books: int = 50, total_subject: int = 200) -> None:
    #     """ Scrapes ocean of pdf, it will take longer time """

    #     if not isinstance(headless, bool):
    #         raise ValueError("[ Snippy ] Headless must be a boolean")

    #     if not isinstance(agent, dict):
    #         raise ValueError("[ Snippy ] Agent must be a dictionary containing 'user_agent' and 'headers'.")

    #     if "user_agent" not in agent or "headers" not in agent:
    #         raise KeyError("[ Snippy ] Agent dictionary must include both 'user_agent' and 'headers' keys.")
        
    #     # if self.file_manager.is_file_exist() and self.file_manager.is_file_exist(open_category) and self.file_manager.is_file_exist(open_category_book):
    #     #     block_list: Dict = self.file_manager.load_json(closed_category)
    #     #     open_list: Dict = self.file_manager.load_json(open_category)
    #     #     open_book_list: Dict = self.file_manager.load_json(open_category_book)

    #     self.target.setup(block_list, open_list, open_book_list, book_limit = total_books, subject_limit = total_subject)

    #     existing_genre_data: Dict = asyncio.run(self.target.scrape(agent, headless))

    #     return existing_genre_data


    def validate_openlibrary_category_links(self, agent: Dict[str, str | Dict[str, str]], headless: bool = True, total_books: int = 50, total_subject: int = 200, total_tabs: int = 1) -> None:
        if not isinstance(headless, bool):
            raise ValueError("[ Snippy ] Headless must be a boolean")

        if not isinstance(agent, dict):
            raise ValueError("[ Snippy ] Agent must be a dictionary containing 'user_agent' and 'headers'.")

        if "user_agent" not in agent or "headers" not in agent:
            raise KeyError("[ Snippy ] Agent dictionary must include both 'user_agent' and 'headers' keys.")

    def reset_data(self, include_chache: bool = False) -> None:
        """ Resets All Data Including Cache datas """
        if include_chache:
            if self.file_manager.is_file_exist(CLOSED_BOOK_PATH):
                self.file_manager.save_json(CLOSED_BOOK_PATH, CLOSED_BOOK_LINKS_FIELD)
                print("[ Snippy ] Open Library Cached Data Reset on Closed Book Links ")
            else:
                print(f"[ Snippy ] Open Library File Path {CLOSED_BOOK_PATH} is not existed")
            
            if self.file_manager.is_file_exist(OPEN_BOOK_PATH):
                self.file_manager.save_json(OPEN_BOOK_PATH, OPEN_BOOK_LINKS_FIELD)
                print("[ Snippy ] Open Library Cached Data Reset on Open Book Links ")
            else:
                print(f"[ Snippy ] Open Library File Path {OPEN_BOOK_PATH} is not existed")


            if self.file_manager.is_file_exist(OPEN_SUBJECT_PATH):
                self.file_manager.save_json(OPEN_SUBJECT_PATH, OPEN_SUBJECT_LINKS_FIELD)
                print("[ Snippy ] Open Library Cached Data Reset on Open Subject Links ")
            else:
                print(f"[ Snippy ] Open Library File Path {OPEN_SUBJECT_PATH} is not existed")
        
        if self.file_manager.is_file_exist(SHELF_AUTHOR_PATH):
            self.file_manager.save_json(SHELF_AUTHOR_PATH, SHELF_AUTHOR_FIELD)
            print(f"[ Snippy ] Open Library shelf author data has been reset")
        else:
            print(f"[ Snippy ] Open Library File Path {SHELF_AUTHOR_PATH} is not existed")
        
        if self.file_manager.is_file_exist(SHELF_BOOK_PATH):
            self.file_manager.save_json(SHELF_BOOK_PATH, SHELF_BOOK_FIELD)
            print(f"[ Snippy ] Open Library shelf book data has been reset")
        else:
            print(f"[ Snippy ] Open Library File Path {SHELF_BOOK_PATH} is not existed")

        if self.file_manager.is_file_exist(SHELF_CATEGORIES_PATH):
            self.file_manager.save_json(SHELF_CATEGORIES_PATH, SHELF_CATEGORIES_FIELD)
            print(f"[ Snippy ] Open Library shelf categories data has been reset")
        else:
            print(f"[ Snippy ] Open Library File Path {SHELF_CATEGORIES_PATH} is not existed")

        if self.file_manager.is_file_exist(SHELF_PUBLISHER_PATH):
            self.file_manager.save_json(SHELF_PUBLISHER_PATH, SHELF_PUBLISHER_FIELD)
            print(f"[ Snippy ] Open Library shelf publisher data has been reset")
        else:
            print(f"[ Snippy ] Open Library File Path {SHELF_PUBLISHER_PATH} is not existed")

        if self.file_manager.is_file_exist(SHELF_PATH):
            self.file_manager.save_json(SHELF_PATH, SHELF_FIELD)
            print(f"[ Snippy ] Open Library shelf shelves data has been reset")
        else:
            print(f"[ Snippy ] Open Library File Path {SHELF_PATH} is not existed")

        print()
        if not include_chache:
            print("[ Snippy ] all of the Open Library data has been reset cleaned")
        else:
            print("[ Snippy ] all of the Open Library data including cache has been reset cleaned")

if __name__ == "__main__":
    controller = OpenLibraryController(None)