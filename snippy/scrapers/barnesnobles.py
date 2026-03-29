import re
import time
import uuid
import random
import asyncio

from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Any, Literal

from playwright_stealth import Stealth
from playwright.async_api import async_playwright, Page, BrowserContext, Locator, TimeoutError

from ..file import FileManager


class BarnesNobles:
    """ """
    def __init__(self, file_manager: FileManager):
        self.target_link = "https://www.barnesandnoble.com/"

        self.file_manager = file_manager
        self.helper = BarnesNobleshelper(self, self.file_manager)

        self.test_path = Path("snippy/scrapers/test.txt").read_text(encoding = 'utf-8')

        self.closed_category: Dict = None
        self.open_category: Dict = None
        self.open_category_book: Dict = None
        
        self.subject_limit: int = 200
        self.book_limit: int = 30

        self.tabs: int = 5

        self.scrape_type: str | List = None

        self.specific_links: str | List = None

        self.shelf_data = []

        self.books_data = []
        self.books_publisher = []
        self.books_categories_data = []
        self.books_author_data = []
    

    def setup(self, block_list: Dict, open_list: Dict, open_book_list, books_data: Dict, books_publisher_data: Dict, books_categories_data: Dict, books_author_data: Dict, book_shelf_data: Dict, book_limit: int = 50, subject_limit: int = 50, scrape_type: Literal["--all", "--book_list_links", "--subject_list_links", "--book_data"] | List = "--book_link", links: List | str = None) -> List:
        """ 
        Setup class attrbiutes
        
        ### Commands:

        * --book_list_links - scrapes book list links within the page range
        * --subject_list_links - scrapes book subject links within the page range  
        * --book_data - scrape books data within the book page range
        * --all - scrapes all of the above

        """

        self.closed_category = block_list
        self.open_category = open_list
        self.open_category_book = open_book_list

        self.subject_limit = subject_limit
        self.book_limit = book_limit

        self.specific_links = links

        self.shelf_data = book_shelf_data

        self.books_data = books_data
        self.books_publisher = books_publisher_data
        self.books_author_data = books_author_data
        self.books_categories_data = books_categories_data

        if "--all" in scrape_type:
            self.scrape_type = ["--subject_list_links", "--book_list_links",  "--book_data"]
            return

        self.scrape_type = scrape_type


    async def scrape(self, agent: Dict[str, str | Dict[str, str]], headless: bool) -> None:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=headless)

            # Apply Snippy's custom user agent
            context = await browser.new_context(
                user_agent=agent["user_agent"],
                extra_http_headers=agent["headers"],
                permissions=["geolocation"],  
                geolocation={"latitude": 40.7128, "longitude": -74.0060},
                locale="en-US"
            )

            # * MAIN GRAB'S SUBJECT, BOOK LINKS
            await context.grant_permissions(
                ["geolocation"],
                origin="https://www.barnesandnoble.com"
            )

            book_links: List = await self.scrape_links(browser_context = context)

            # * MAIN GRAB'S BOOK DATA'S OR METADATA'S
            book_datas: List = await self.scrape_book_data(links = book_links, browser_context = context)

            await context.close()
            await browser.close()

            return book_datas


    async def scrape_links(self, browser_context: BrowserContext) -> None:
        # * Scrape only subject page of openlibrary
        if len(self.open_category["subjects"]) == 0 and "--subject_list_links" in self.scrape_type:
            print("[ Snippy ] Locating subject book list links within the page . . . ")

            # * GRABS SUBJECT LINKS AS A STARTER
            page = await browser_context.new_page()
            await self.helper.grab_subject_links(page, goto_link=f"{self.target_link}/subjects/")
            await page.close()

            # * GRABS SUBJECT'S BOOK LINKS
            subject_links = [s["subject_link"] for s in self.open_category["subjects"][:self.tabs]]


        if "--book_list_links" in self.scrape_type:
            print("[ Snippy ] Locating book list links within the page . . .")
            if self.specific_links and "--subject_list_links" in self.specific_links:
                tasks = [self.helper.grab_book_links(page = await browser_context.new_page(), goto_link=link) for link in subject_links]

                await asyncio.gather(*tasks)

            if self.specific_links and isinstance(self.specific_links, list):
                tasks = [self.helper.grab_book_links(page=await browser_context.new_page(), goto_link=link) for link in self.specific_links]

                await asyncio.gather(*tasks)

            if self.specific_links and isinstance(self.specific_links, str):
                await self.helper.grab_book_links(page = await browser_context.new_page(), goto_link = self.specific_links)

        return self.open_category_book["books"]


    async def scrape_book_data(self, links: str | List, browser_context: BrowserContext) -> None:
        if "--book_data" in self.scrape_type:
            print("[ Snippy ] Locating book data within the page . . .")

            links = await self.helper.split_list(links, self.tabs)

            tasks = [self.helper.grab_book_data(page=await browser_context.new_page(), goto_links = list_links) for list_links in links]
            
            await asyncio.gather(*tasks)

            print(self.shelf_data)

            

class BarnesNobleshelper:
    """ """
    def __init__(self, parent: BarnesNobles, file_manager: FileManager):
        self.file_manager = file_manager

        self.parent = parent
        self.file_manager = file_manager

        self.test_path = Path("snippy/scrapers/test.txt").read_text(encoding = 'utf-8')

    async def scroll_and_wait(self, page):
        for _ in range(10):
            await page.mouse.wheel(0, 1000)  
            await page.wait_for_timeout(500)

    async def split_list(self, lst, n) -> None:
        """ Split list into chunks for parallel tasks. """
        chunks = [[] for _ in range(n)]

        unscripted_items = [(item, i) for i, item in enumerate(lst) if not item.get("is_scraped", False)]

        for i, item in enumerate(unscripted_items):
            chunks[i % n].append(item)

        return chunks


    async def generate_uuid(self, index: int, text_code: str) -> str:
        text_code = text_code.upper()
        raw_uuid = uuid.uuid4().hex.upper()
        return f"{text_code}-{raw_uuid[:4]}{index}{raw_uuid[4:8]}"


    async def normalize_link(self, url: str) -> str:
        """ ormalize Barnes and Noble book URL """
        parsed = urlparse(url)
     
        path = parsed.path

        if ";jsessionid" in path:
            path = path.split(";jsessionid")[0]

        return f"https://www.barnesandnoble.com{path}"


    async def grab_subject_links(self, page: Page, goto_link: str = None) -> List:
        """ Scrapes entire subject links within the page range or area """
        if len(self.parent.open_category["subjects"]) >= self.parent.subject_limit:
            print("[ Snippy ] Subject limit reached.")
            return

        if goto_link:
            await page.goto(goto_link)

        block_list: Dict = self.parent.closed_category
        open_list: Dict = self.parent.open_category

        new_data: int = 0

        links = page.eval_on_selector_all(
            "a[href*='/b/']",
            "elements => elements.map(el => el.href)"
        )


    async def grab_book_links(self, page: Page, goto_link: str = None) -> List:
        """ Scrapes entire book links within the page range or area """
        if self.parent.open_category_book["total_book_not_scraped"] >= self.parent.book_limit:
            print("[ Snippy ] Book Link Limit Reached. ")
            return

        if goto_link:
            await page.goto(goto_link)

        book_links = await page.eval_on_selector_all(
            "a[href*='/w/']",
            "els => els.map(el => el.href)"
        )

        new_data = 0

        for link in book_links:
            data: Dict = {
                "book_link":  await self.normalize_link(link),
                "is_scraped": False
            }

            if data not in self.parent.open_category_book["books"] and len(self.parent.open_category_book["books"]) != self.parent.book_limit:
                self.parent.open_category_book["books"].append(data)

                new_data += 1
        
        if new_data:
            print("[ Snippy ] New Book Link Data Added: ", new_data)
        else:
            print("[ Snippy ] No Book Added")

        self.parent.open_category_book["date_updated"] = datetime.today().strftime('%Y-%m-%d')
        self.parent.open_category_book["total_book_not_scraped"] = sum(1 for book in self.parent.open_category_book["books"] if book.get("is_scraped") is False)
        self.parent.open_category_book["total_book_links"] = len(self.parent.open_category_book["books"])

        self.file_manager.save_json("snippy/cache/barnesnobles/open_category_links/barnesnobles_books.json", self.parent.open_category_book)
        
        await page.close()
        return self.parent.open_category_book["books"]


    async def grab_book_data(self, page: Page, goto_links: List = None) -> Dict:
        """ Scrape entire book preview page range or area """

        for goto_link in goto_links:

            time.sleep(random.choice([1,2,3,4,5,6]))
            await page.goto(goto_link[0]["book_link"])

            index = goto_link[1]


            # * CHECKS IF NO RESULT PAGE POPS UP
            await self.scroll_and_wait(page)

            no_result = await page.evaluate("!!document.querySelector('.no-search-msg.mb-m')")

            if no_result:
                self.parent.open_category_book["books"][index]["is_scraped"] = True
                self.parent.open_category_book["total_book_not_scraped"] -= 1
                continue 

            shelf_data: Dict = {
                "book_id": None,
                "book_author_id": None,
                "book_categories_id": None,
                "book_publisher_id": None 
            }

            shelf_data["book_id"] = await self.grab_book_metadata(page, goto_link[0], index)

            shelf_data["book_author_id"] = await self.grab_book_author(page, index)

            shelf_data["book_categories_id"] = await self.grab_book_genre(page, index)

            shelf_data["book_publisher_id"] = await self.grab_book_publisher(page, index)

            self.parent.open_category_book["books"][goto_link[1]]["is_scraped"] = True 
            self.parent.open_category_book["total_book_scraped"] += 1
            self.parent.open_category_book["total_book_not_scraped"] -= 1

            if shelf_data not in self.parent.shelf_data["books"]:
                self.parent.shelf_data["books"].append(shelf_data)
                self.parent.shelf_data["total_books"] += 1


            self.file_manager.save_json("snippy/data/barnesnobles_shelf/shelf.json", self.parent.shelf_data)
            self.file_manager.save_json("snippy/data/barnesnobles_shelf/book.json", self.parent.books_data)
            self.file_manager.save_json("snippy/data/barnesnobles_shelf/author.json", self.parent.books_author_data)
            self.file_manager.save_json("snippy/data/barnesnobles_shelf/publisher.json", self.parent.books_publisher)
            self.file_manager.save_json("snippy/data/barnesnobles_shelf/categories.json", self.parent.books_categories_data)

            self.file_manager.save_json("snippy/cache/barnesnobles/open_category_links/barnesnobles_books.json", self.parent.open_category_book)

                
        await page.close()

        self.parent.open_category_book["date_updated"] = datetime.today().strftime('%Y-%m-%d')
        self.parent.shelf_data["date_updated"] = datetime.today().strftime('%Y-%m-%d')

        


    async def grab_book_publisher(self, page: Page, index: int) -> None:
        """ Grabs book publisher """
        publisher_el = await page.query_selector("tr:has(th:has-text('Publisher:')) td a")

        if publisher_el:
            publisher_name = (await publisher_el.inner_text()).strip()
            href = await publisher_el.get_attribute("href")

            if href and not href.startswith("http"):
                href = f"https://www.barnesandnoble.com{href}"

            for pub in self.parent.books_publisher["publishers"]:
                if pub["url"] == href:
                    return pub["_id"]

            _id: str = await self.generate_uuid(index, "PUB")

            data = {
                "_id": _id,
                "name": publisher_name,
                "url": href
            }

            if data not in self.parent.books_publisher["publishers"]:
                self.parent.books_publisher["publishers"].append(data)
                self.parent.books_publisher["total_publishers"] += 1

            return _id


    async def grab_book_genre(self, page: Page, index: int) -> List[str]:
        """ Grabs book genres """
        
        genre = []

        genre_elements = await page.query_selector_all(".related-subject-container a")

        for el in genre_elements:
            name = (await el.inner_text()).strip()
            href = await el.get_attribute("href")

            if href and not href.startswith("http"):
                href = f"https://www.barnesandnoble.com{href}"

            existing = next((cat for cat in self.parent.books_categories_data["categories"] if cat["url"] == href), None)

            if existing:
                genre.append(existing["_id"])
            else:
                _id: str = await self.generate_uuid(index, "CAT")
                data = {
                    "_id": _id,
                    "name": name,
                    "url": href
                }

                self.parent.books_categories_data["categories"].append(data)
                self.parent.books_categories_data["total_categories"] += 1
                genre.append(_id)
        
        return genre
            
      
    async def grab_book_author(self, page: Page, index: int) -> str:
        """ Grabs book author metadata """
        _id: str = await self.generate_uuid(index, "AUTHOR")

        author_metadata = {
            "url": None,
            "image_cover_url": None,
            "name": None,
            "about": None,
            "hometown": None,
            "birthdate": None,
            "birth_place": None
        }

        # * GRABS AUTHOR IMAGE COVER
        img_el = await page.query_selector(".col-lg-4 img")

        if img_el:
            src = await img_el.get_attribute("src")
            author_metadata["image_cover_url"] = src

        # * GRABS AUTHOR HREF AND NAME
        try:
         
            container = await page.query_selector("#pdp-header-info")

            if container:
                author_el = await container.query_selector("a[href*='/b/contributor/'], a[href*='/s/%22']")

                if author_el:
                    name = (await author_el.inner_text()).strip()
                    author_metadata["name"] = name

                    href = await author_el.get_attribute("href")

                    if href:
                        
                        author_metadata["url"] = f"https://www.barnesandnoble.com{href.replace(" ", "_")}"
        except:
            pass 
        
        # * GRABS HOME TOWN, BRITHDATE , BIRTH PLACE
        about_task = None
        try:
            if await page.query_selector("div.expandable-section div.text--medium"):
                about_task = page.eval_on_selector(
                    "div.expandable-section div.text--medium",
                    "el => el.textContent"
                )
        except Exception:
            about_task = None

        info_blocks_task = page.eval_on_selector_all(
            "div.col-lg-6",
            """els => els.map(el => {
                const label = el.querySelector('p')?.innerText.trim();
                const value = el.querySelector('span')?.innerText.trim();
                return label && value ? [label, value] : null;
            }).filter(Boolean)"""
        )
        
        if about_task:
            about, info_blocks = await asyncio.gather(about_task, info_blocks_task)
        else:
            about = None
            info_blocks = await info_blocks_task

        if about:
            author_metadata["about"] = about

        for label, value in info_blocks:
            if "Hometown" in label:
                author_metadata["hometown"] = value
            elif "Date of Birth" in label:
                author_metadata["birthdate"] = value
            elif "Place of Birth" in label:
                author_metadata["birth_place"] = value

        for existing in self.parent.books_author_data["authors"]:
            if (existing["name"] == author_metadata["name"] and existing.get("url") == author_metadata.get("url")):
                return existing["_id"]
        
        _id: str = await self.generate_uuid(index, "AUTHOR")
        author_metadata["_id"] = _id

        self.parent.books_author_data["authors"].append(author_metadata)
        self.parent.books_author_data["total_authors"] += 1

        return _id  

       
    async def grab_book_metadata(self, page: Page, link: str, index: int) -> str:
        """ grabs entire book metadata """

        _id: str = await self.generate_uuid(index, "BOOK")

        metadata = {
            "_id": _id,
            "url": None,
            "title": None,
            "description": None,
            "cover_image_url": None,
            "published_date": None,
            "isbn_10": None,
            "isbn_13": None,
            "page_count": 0,
            "language": None,
            "rating_count": 0,
            "rating_average": 0,
        }

        # * JUST GRAB THE URL PARAMS THAT USED ON GOTO LINK
        metadata["url"] = link["book_link"]

        # * GRABS BOOK TITLE
        metadata["title"] = await page.text_content("h1[itemprop='name']")

        # * GRABS BOOK DESCRIPTION
        try:
            description = await page.eval_on_selector(
                "div[itemprop='description']",
                "el => el.innerText.trim()"
            )
        except:
            description = None

        if description:
            metadata["description"] = re.sub(r'\s+', ' ', description)

        # * GRABS THE IMAGE COVER LINK
        img_url = await page.get_attribute("img#pdpMainImage", "src")
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        
        metadata["cover_image_url"] = img_url

        # * GRABS ISBN-13, ISBN-10, PUBLISHED DATE, PAGE COUNT
        rows = await page.query_selector_all("table.plain.centered tr")
        
        for row in rows:
            th = await row.query_selector("th")
            td = await row.query_selector("td")

            if not th or not td:
                continue

            label = (await th.text_content()).strip().lower()
            value = (await td.text_content()).strip()

            if "isbn-13" in label:
                metadata["isbn_13"] = value

            elif "isbn-10" in label:
                metadata["isbn_10"] = value

            elif "pages" in label:
                try:
                    metadata["page_count"] = int(value)
                except:
                    metadata["page_count"] = None

            elif "publication date" in label:
                metadata["published_date"] = value

        metadata["language"] = "en"


        # * GRABS RATING + REVIEW COUNT
        rating_block = await page.query_selector("dl.bv-stars-container")

        if rating_block:
            rating_html = await rating_block.inner_html()
            rating_match = re.search(r'<dd class="bv-rating-ratio-number">.*?([\d.]+).*?</dd>', rating_html, re.S)
            rating_average = float(rating_match.group(1)) if rating_match else 0.0

            count_match = re.search(r'(\d+)\s+Review[s]?', rating_html, re.S)
            rating_count = int(count_match.group(1)) if count_match else 0
        else:
            rating_average = 0
            rating_count = 0

        metadata["rating_average"] = rating_average
        metadata["rating_count"] = rating_count

        if metadata not in self.parent.books_data["books"]:
            self.parent.books_data["books"].append(metadata)
            self.parent.books_data["total_books"] += 1

        print("Added New Data: ", metadata["title"])

        return _id


if __name__ == "__main__":
    pass


    """
    Respecting Barnes & Nobles Website

    User-agent: *
    Disallow: /account/
    Disallow: /mobile/account/
    Disallow: /checkout/
    Disallow: /mobile/checkout/
    Disallow: */lia.barnesandnoble/
    Disallow: /ajax?
    Disallow: /www/search?
    Disallow: /handler.jsp
    Disallow: /google/ad
    Disallow: /cartridges/
    Disallow: /includes/
    Disallow: /noresults/

    Disallow: /s/
    Sitemap: https://www.barnesandnoble.com/sitemap.xml
    """