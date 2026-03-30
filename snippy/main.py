import random

from typing import List, Dict

from .controllers import *
from .file import FileManager


# * INSTANCIATE ONLY ONCE
file_manager = FileManager()

precaution = PrecautionController(file_manager)
ocean_of_pdf = OpenLibraryController(file_manager)
barnes_and_nobles = BarnesNoblesController(file_manager)


def generate_agent() -> Dict[str, str | Dict[str, str]]:
    """ Randomly picks user agent """
    user_agents: List = file_manager.load_json(file_name = "snippy/cache/user_agents.json")

    return {
        "user_agent": random.choice(user_agents),
        "headers": {
            "From": "https://github.com/Vince9090",
            "X-Snippy-Bot": "SnippyBot/1.0 (contact: seeksnippy@gmail.com)",
            "X-Snippy-Purpose": "Student project for making search engine about books, original data source will be credited to the site."
        }
    }


def seek_checkup(headless: bool = True) -> None:
    """ Runs a stealth test on Snippy to see if it's detectable. """
    result: bool = precaution.validate_checkup(
        agent = generate_agent(),
        headless = headless
    )

    if result:
        print(r"[ Snippy ] Sucessfully take snippy to a checkup results are in snippy/cache/daily_checkup folder. 🎉")
    else:
        print("[ Snippy ] Snippy checkup did not complete successfully.")

    return result

# * ------------------------------------------------------ OPEN LIBRARY ----------------------------------------------------- * #

def seek_openlibrary_scraped_data() -> List:
    """ Gets the existing data of openlibrary """
    result: List = file_manager.load_json(file_name="snippy/data/shelf.json")

    if result:
        print("[ Snippy ] Sucessfully take snippy scraped Open Library data. 🥳🎉")

    else:
        print("[ Snippy ] Snippy scraped Open Library did not complete. 😐✌️")
    
    return result

def seek_openlibrary(headless: bool = True, total_books: int = 50, total_subject: int = 200, total_tabs: int = 3) -> List:
    """ Scrapes open library online and it will take longer time """
    result: List = ocean_of_pdf.validate_openlibrary(
        agent = generate_agent(),
        headless = headless,
        total_books = total_books,
        total_subject = total_subject
    )

    if result:
        print("[ Snippy ] Sucessfully take snippy to scrape Open Library. 🥳🎉")
    else:
        print("[ Snippy ] Snippy scraping on Open Library did not complete successfully. 😐✌️")

    return result


def seek_openlibrary_book_list(link: str | List[str], online: bool = True) -> List:
    """ Scrape open library book list page range or area """
    pass


def seek_openlibrary_book(link: str | List[str], online: bool = True) -> Dict | List:
    """ Scrape open library book page range or area """
    pass

# * ------------------------------------------------------ ------------ ----------------------------------------------------- * #



# * ---------------------------------------------------- BARNES & NOBLES ---------------------------------------------------- * #

def seek_barnesnobles(online: bool = True, headless: bool = True, total_books: int = 50, total_subject: int = 200, total_tabs: int = 3) -> List:
    """ Scrape barnes and nobles full range, it will take longer time """
    if online:
        result: List = barnes_and_nobles.validate_barnesnobles(
            agent = generate_agent(),
            type = "--all",
            headless=headless,
            total_books=total_books,
            total_subject=total_subject
        )

        if result:
            print("[ Snippy ] Sucessfully take snippy to scrape Barnes and Nobles. 🥳🎉")
        else:
            print("[ Snippy ] Snippy scraping on Barnes and Nobles did not complete successfully. 😐✌️")

    else:

        result: List = file_manager.load_json(file_name="snippy/data/shelf.json")

        if result:
            print("[ Snippy ] Sucessfully take snippy scraped Barnes and Nobles data. 🥳🎉")

        else:
            print("[ Snippy ] Snippy scraped Barnes and Nobles did not complete. 😐✌️")

    return result


def seek_barnesnobles_book_list(link: str | List[str], online: bool = True, headless: bool = True, total_books: int = 50) -> List:
    """ Scrape barnes and nobles book list page """
    if online:
        result: List = barnes_and_nobles.validate_barnesnobles(
            agent=generate_agent(),
            type = "--book_list_links",
            headless=headless,
            total_books=total_books,
            specific_link = link
        )

        if result:
            print("[ Snippy ] Sucessfully take snippy to scrape Barnes and Nobles. 🥳🎉")
        else:
            print(
                "[ Snippy ] Snippy scraping on Barnes and Nobles did not complete successfully. 😐✌️")

    else:

        result: List = file_manager.load_json(file_name="snippy/data/shelf.json")

        if result:
            print(
                "[ Snippy ] Sucessfully take snippy scraped Barnes and Nobles data. 🥳🎉")

        else:
            print("[ Snippy ] Snippy scraped Barnes and Nobles did not complete. 😐✌️")


def seek_barnesnobles_book(link: str | List[str], online: bool = True, headless: bool = True) -> Dict | List:
    """ Scrape barnes and nobles book details page """
    if online:
        result: List = barnes_and_nobles.validate_barnesnobles(
            agent=generate_agent(),
            type="--book_data",
            headless=headless,
            specific_link=link
        )

        if result:
            print("[ Snippy ] Sucessfully take snippy to scrape Barnes and Nobles. 🥳🎉")
        else:
            print("[ Snippy ] Snippy scraping on Barnes and Nobles did not complete successfully. 😐✌️")

    else:

        result: List = file_manager.load_json(
            file_name="snippy/data/shelf.json")

        if result:
            print("[ Snippy ] Sucessfully take snippy scraped Barnes and Nobles data. 🥳🎉")
        else:
            print("[ Snippy ] Snippy scraped Barnes and Nobles did not complete. 😐✌️")

# * ---------------------------------------------------- --------------- ---------------------------------------------------- * #


if __name__ == "__main__":
      file_manager.save_json(data = "uwu", file_name = "snippy/data/daily_scraped.json")

      """
      Sources:

      Website Scraped:
        Web Novel: https://www.webnovel.com/
        Ocean of PDF: https://oceanofpdf.com/
      
      Stealth:
        Github: https://github.com/Mattwmaster58/playwright_stealth
      """