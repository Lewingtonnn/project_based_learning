import time
import re

from playwright.sync_api import sync_playwright, Page, expect


def run_playwright_script():
    timestart = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://playwright.dev/")
        print(page.title())
        page.screenshot(path="playwright_screenshot.png")
        browser.close()
    timestop = time.time()
    elapsed_time = f"It took {timestop - timestart} seconds to run the script"
    print(elapsed_time)
from playwright_as
from playwright.async_api import async_playwright
async def run_playwright_async_script():
    timestart = time.time()
    async with async_playwright() as n:
        browser = await n.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://playwright.dev/")
        await page.wait_for_load_state("networkidle")
        print(await page.title())
        await page.screenshot(path="playwright_screenshot_async.png")
        await browser.close()
    timestop = time.time()
    elapsed_time = f"It took {timestop - timestart} seconds to run the script"
    print(elapsed_time)

def test_has_title(page:Page):
    page.goto("https://playwright.dev/")
    expect(page).to_have_title(re.compile("Playwright"))
    print("Test passed: Page has the expected title.")

def testget_link(page:Page):
    page.goto("https://www.playwright.dev/")
    page.get_by_role("link", name="Get started").click()
    expect(page.get_by_role("heading", name="Installation")).to_be_visible()



if __name__ == "__main__":
    run_playwright_script()
    import asyncio; asyncio.run(run_playwright_async_script())
    # test_get_link()
    # test_has_title()
