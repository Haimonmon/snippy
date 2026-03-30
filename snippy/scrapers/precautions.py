from typing import Dict
from datetime import datetime

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


class Precaution:
    """
    Provide a test record for the snippy bot

    ### Methods:
    take_screenshot() -> None

        takes snippy for a detection test
    """
    
    def __init__(self, file_manager):
        self.target_link = "https://bot.sannysoft.com/"


    def checkup(self, agent: Dict[str, str | Dict[str, str]], headless: bool) -> bool:
        """ Takes a screenshot of the sannysoft website for bot test detection """
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(headless = headless)

            context = browser.new_context(
                user_agent = agent["user_agent"], 
                extra_http_headers = agent["headers"]
            )

            page = context.new_page()

            page.goto(self.target_link)
            page.screenshot(path = f"snippy/cache/daily_checkup/test-snippy-checkup-{datetime.today().strftime('%Y-%m-%d')}.png")

            context.close()
            browser.close()

            return True


if __name__ == "__main__":
    precaution = Precaution()

    precaution._take_test()

    """
    Source:
        Playwright Stealth: https://github.com/Mattwmaster58/playwright_stealth

    """