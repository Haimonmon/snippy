import time
import random
import asyncio

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Literal

from playwright_stealth import Stealth
from playwright.async_api import async_playwright, Page, BrowserContext, Locator, TimeoutError

from ..file import FileManager


class OpenLibrary:
    """ Scraping book's on official ocean of pdf website """

    def __init__(self, file_manager: FileManager):
        self.target_link = "https://openlibrary.org"

        self.file_manager = file_manager
        self.helper = OpenLibraryHelper(self, self.file_manager)

        self.test_path = Path("snippy/scrapers/test.txt").read_text(encoding = 'utf-8')

        self.blocked_links: Dict = None
        self.book_links: Dict = None
        self.subject_links: Dict = None
        
        self.subject_limit: int = 0
        self.book_limit: int = 0

        self.tabs = 3

    def setup(self, block_links: Dict, book_links: Dict, subject_links, book_limit: int = 50, subject_limit: int = 50, tabs: int = 1) -> List:
        """ Setup class attrbiutes """
        self.book_links = book_links
        self.blocked_links = block_links
        self.subject_links = subject_links

        self.book_limit = book_limit
        self.subject_limit = subject_limit

        self.tabs = tabs

    async def scrape_cache(self, agent: Dict, headless: bool) -> Dict:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=headless)

            context = await browser.new_context(
                user_agent=agent["user_agent"],
                extra_http_headers=agent["headers"]
            )

            book_links: List = await self.scrape_links(browser_context = context)

            await context.close()
            await browser.close()

            return book_links

    async def scrape(self, agent: Dict[str, str | Dict[str, str]], headless: bool) -> Dict:
        """ Scrape books online on Open Library Website """
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=headless)

            # Apply Snippy's custom user agent
            context = await browser.new_context(
                user_agent=agent["user_agent"],
                extra_http_headers=agent["headers"]
            )

            # * MAIN GRAB'S SUBJECT, BOOK LINKS
            book_links: List = await self.scrape_links(browser_context = context)

            # * MAIN GRAB'S BOOK DATA'S OR METADATA'S
            book_datas: List = await self.scrape_book_data(book_links, browser_context = context)

            await context.close()
            await browser.close()

            return book_datas


    async def scrape_links(self, browser_context: BrowserContext) -> List:
        """ Scrape ocean of pdf's genre """
        # * Scrape only subject page of openlibrary
        if len(self.subject_links["subject_links"]) == 0:

            # * GRABS SUBJECT LINKS AS A STARTER
            page = await browser_context.new_page()
            await self.helper.grab_subject_links(page, goto_link = f"{self.target_link}/subjects/")
            page.close()

        # * GRABS SUBJECT'S BOOK LINKS
        subject_links = [s["subject_link"] for s in self.subject_links["subject_links"][:self.tabs]]

        tasks = [self.helper.grab_book_links(await browser_context.new_page(), goto_link=link) for link in subject_links]

        await asyncio.gather(*tasks)

        return self.book_links["books"]
        

    async def scrape_book_data(self, book_links: List, browser_context: BrowserContext) -> None:
        """ Gets Book Data """
        page: Page = await browser_context.new_page()

        await page.set_content(self.test_path)

        # * PRIORITIZE LINKS
        await self.helper.grab_subject_links(page)
        await self.helper.grab_book_links(page)

        # * GRAB BOOK METADATA'S
        book_metadata: List = await self.helper.grab_book_metadata(page)

        return book_metadata


class OpenLibraryHelper:
    """ Helper class which contains the scraping content """
    def __init__(self,parent: OpenLibrary,  file_manager: FileManager):
        self.parent = parent
        self.file_manager = file_manager

        self.test_path = Path("snippy/scrapers/test.txt").read_text(encoding = 'utf-8')


    async def normalize_subject_link(self, text: str, href: str) -> str:
        """ Best for avoiding /search links or href's """
        if href.startswith("/subjects/"):
            return f"https://openlibrary.org{href}"
        
        elif href.startswith("/search"):
            slug = text.strip().lower().replace(" ", "_")
            return f"https://openlibrary.org/subjects/{slug}"
        
        return None


    async def safe_fetch(self, locator: Locator, method: Literal["inner_text", "get_attribute"] = "inner_text", attr: str = None, timeout: int = 1000, eval_all: str = None, default: Any = "No Data") -> Any:
        """ Universal safe fetch function for Playwright locators. """
        try:
            if eval_all:
                result = await locator.evaluate_all(eval_all)
                return result if result else default
            elif method == "inner_text":
                text = (await locator.inner_text(timeout=timeout)).strip()
                return text if text else default
            elif method == "get_attribute" and attr:
                value = await locator.get_attribute(attr, timeout=timeout)
                return value if value else default
            else:
                return default
        except TimeoutError:
            return default
        

    async def grab_subject_links(self, page: Page, goto_link: str = None) -> None:
        """ Grabs subject header links or also known genre's too. """
        # page.set_content(self.parent.test_path)

        if len(self.parent.open_category["subjects"]) >= self.parent.subject_limit:
            print("[ Snippy ] Subject limit reached.")
            return

        if goto_link:
            await page.goto(goto_link)

        block_list: Dict = self.parent.closed_category
        open_list: Dict = self.parent.open_category

        new_data: int = 0

        links = page.locator('a[href*="/subjects/"], a[href*="/search"][href*="subject%3A"]')
        count: int = await links.count()

        for i in range(count):
            link = links.nth(i)
            text: str = (await link.inner_text()).strip()
            href: str = await link.get_attribute("href")

            normalized_href: str = await self.normalize_subject_link(text = text, href = href)

            if normalized_href:
                subject_data: Dict = {
                    "subject_name": text,
                    "subject_link": normalized_href
                }

                if subject_data not in open_list["subjects"] and subject_data not in block_list["subjects"] and len(open_list["subjects"]) != self.parent.subject_limit:
                    open_list["subjects"].append(subject_data)
                    new_data += 1

        open_list["total_subjects"] = len(open_list["subjects"])
        open_list["date_updated"] = datetime.today().strftime('%Y-%m-%d')

        self.file_manager.save_json("snippy/cache/openlibrary/open_category_links/openlibrary.json", open_list)

        self.parent.open_category = open_list

        print(f"[ Snippy ] New data added: {new_data}")


    async def grab_book_links(self, page: Page, goto_link: str = None, max_clicks: int = 10) -> None:
        """ Scrape book links for caching """
        if self.parent.open_category_book["total_active_book_links"] >= self.parent.book_limit:
            print("[ Snippy ] Book Link Limit Reached. ")
            return

        time.sleep(10)

        if goto_link:
            await page.goto(goto_link)

        await self.grab_subject_links(page)

        book_cards = page.locator('a[href^="/books/"]')
        next_btn = page.locator('button.slick-next')

        clicks = 0

        new_data = 0

        while True:
            hrefs = await book_cards.evaluate_all("els => els.map(e => e.getAttribute('href'))")
            for href in hrefs:
                data: Dict = {
                    "book_link": f"https://openlibrary.org{href}",
                    "is_scraped": False
                }

                if data not in self.parent.open_category_book["books"] and len(self.parent.open_category_book["books"]) != self.parent.book_limit:
                    self.parent.open_category_book["books"].append(data)
                    new_data += 1

            disabled = await next_btn.get_attribute("aria-disabled")
            disabled = (disabled or "").lower()

            if disabled == "true" or clicks >= max_clicks or len(self.parent.open_category_book["books"]) >= self.parent.book_limit:
                print("[ Snippy ] Scraping book link stopped")
                break

            await next_btn.click()
            await page.wait_for_timeout(random.choice([1000, 500, 1500]))

            clicks += 1
            # print(clicks)

        if new_data:
            print("[ Snippy ] New Book Link Data Added: ", new_data)
        else:
            print("[ Snippy ] No Book Added")

        self.parent.open_category_book["date_updated"] = datetime.today().strftime('%Y-%m-%d')
        self.parent.open_category_book["total_book_not_scraped"] = sum(1 for book in self.parent.open_category_book["books"] if book.get("is_scraped") is False)
        self.parent.open_category_book["total_book_links"] = len(self.parent.open_category_book["books"])

        self.file_manager.save_json("snippy/cache/openlibrary/open_category_links/openlibrary_books.json", self.parent.open_category_book)

        await page.close()
        return self.parent.open_category_book["books"]
    

    async def grab_book_metadata(self, page: Page, goto_link: str = None) -> Dict:
        """ Get's book metadata's """
        data = {}

        block = page.locator('div.work-title-and-author.desktop')

        # * GRABS TITLE, SUBTITLE, AUTHORS
        data["title"] = await self.safe_fetch(block.locator("span > h1.work-title"))
        data["subtitle"] = await self.safe_fetch(block.locator("span > h2.work-subtitle"))
        data["authors"] = await self.safe_fetch(
            block.locator("h2.edition-byline a"),
            eval_all="els => els.map(e => e.textContent.trim())",
            default=[]
        )

        # * GRABS RATING VALUE AND RATING COUNT
        rating_value = await self.safe_fetch(block.locator('meta[itemprop="ratingValue"]'), method="get_attribute", attr="content")
        rating_count = await self.safe_fetch(block.locator('meta[itemprop="ratingCount"]'), method="get_attribute", attr="content")
        data["rating_value"] = float(rating_value) if rating_value else None
        data["rating_count"] = int(rating_count) if rating_count else None

        # * GRABS BOOK STATS
        stats = await self.safe_fetch(
            block.locator("li.reading-log-stat"),
            eval_all='''els => els.map(e => {
                let num = parseInt(e.querySelector(".readers-stats__stat")?.textContent?.trim() || 0);
                let label = e.querySelector(".readers-stats__label")?.textContent?.trim() || '';
                return {label, num};
            })''',
            default=[]
        )

        # ? RE ARRANGE BOOK STATS
        data["stats"] = {}
        for stat in stats:
            key = stat["label"].lower().replace(" ", "_")
            data["stats"][key] = stat["num"]

        # * GRABS DESCRIPTION
        data["description"] = await self.safe_fetch(page.locator('div.read-more__content.markdown-content'))

        block = page.locator('div.edition-omniline')

        # * GRABS PUBLISHED DATE, PUBLISHER, LANGUAGE, NUM OF PAGES
        data["published_date"] = await self.safe_fetch(block.locator('span[itemprop="datePublished"]'))
        publisher_locator = block.locator('div.edition-omniline-item', has_text='Publisher').locator('a')
        data["publisher"] = await self.safe_fetch(publisher_locator)
        data["language"] = await self.safe_fetch(block.locator('span[itemprop="inLanguage"] a'))
        data["num_pages"] = await self.safe_fetch(block.locator('span[itemprop="numberOfPages"]'))
 
        print(data)
        return data


if __name__ == "__main__":
    ocean = OpenLibrary(None)
    
    ocean.scrape_links(
            agent={
                "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
                "headers": {
                    "From": "https://github.com/Vince9090",
                    "X-Snippy-Bot": "SnippyBot/1.0 (contact: seeksnippy@gmail.com)",
                    "X-Snippy-Purpose": "Student project for making search engine about books; credits will be given."
                }
            },
            headless=True
        )
    
    """
    Respect Site robots.txt

    User-agent: *
    Disallow: /api
    Disallow: /edit
    Disallow: /account
    Disallow: /merges
    Disallow: /search
    Disallow: /search/publishers
    Disallow: /search/authors
    Disallow: /search/inside
    Disallow: /search/subjects
    Disallow: /search/lists
    Disallow: /advancedsearch
    Disallow: /publishers
    Disallow: /books/add
    Disallow: /qrcode
    Disallow: */borrow*
    Disallow: /*.rdf$

    Sitemap: https://openlibrary.org/static/sitemaps/siteindex.xml.gz

    User-agent: Baiduspider
    Crawl-delay: 10

    User-agent: Googlebot
    Disallow: /*.rdf$
    Crawl-delay: 10

    User-agent: AhrefsBot
    Crawl-delay: 10

    User-agent: meta-externalagent
    Crawl-delay: 10

    User-agent: anthropic-ai
    Crawl-delay: 10

    User-agent: ClaudeBot
    Crawl-delay: 10

    User-agent: openai
    Crawl-delay: 10

    User-agent: ChatGPT
    Crawl-delay: 10

    User-agent: bingbot
    Crawl-delay: 10

    User-agent: Yandex
    Crawl-delay: 10

    User-agent: *bot
    Crawl-delay: 10
    """