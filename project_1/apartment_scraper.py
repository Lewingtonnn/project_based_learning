import asyncio
import random
import time
import logging
import json
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
import psutil
from metrics import (
    SCRAPER_SUCCESS, SCRAPER_FAILURES, LISTINGS_SCRAPED,
    SCRAPE_DURATION, VALIDATION_FAILURES, DUPLICATE_RECORDS,
    DB_INSERT_FAILURES, RETRIES_ATTEMPTED, MEMORY_USAGE, CPU_USAGE, VALIDATION_SUCCESS
)
# Configure logging for structured output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Global Configurations and Helper Functions ---

# Random Delays: Waits for a random duration to simulate human behavior
async def add_random_delay(min_delay: float = 1, max_delay: float = 5):
    """Waits for a random duration between min_delay and max_delay seconds."""
    delay = random.uniform(min_delay, max_delay)
    logging.info(f"Waiting for {delay:.2f} seconds...")
    await asyncio.sleep(delay)


# User Agents: List of common browser User-Agent strings to randomize requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.86 Mobile Safari/537.36"
]


# --- Safe Extraction Helpers ---
# These functions try to get text/attributes and return 'N/A' if an error occurs or element is not found.

async def safe_inner_text(locator) -> str:
    """Safely gets inner text from a locator, returns 'N/A' on failure."""
    try:
        if await locator.count() > 0:
            text=(await locator.inner_text()).strip()
            return text if text else None
    except Exception as e:
        logging.debug(f"Could not get inner_text: {e}")  # Use debug for non-critical failures
    return None


async def safe_get_attribute(locator, attribute: str) -> str:
    """Safely gets an attribute value from a locator, returns 'N/A' on failure."""
    try:
        if await locator.count() > 0:
            attr_value = await locator.get_attribute(attribute)
            return attr_value.strip() if attr_value else None
    except Exception as e:
        logging.debug(f"Could not get attribute '{attribute}': {e}")
    return None


# --- Retry Strategy for Page Navigation ---
@retry(
    wait=wait_fixed(2),  # Wait 2 seconds between retries
    stop=stop_after_attempt(3),  # Try up to 3 times (1 initial + 2 retries)
    retry=(retry_if_exception_type(PlaywrightError) | retry_if_exception_type(asyncio.TimeoutError)),
    reraise=True  # Re-raise the exception if all retries fail
)

async def scrap_page_with_different_structure(page:Page, url:str, existing_data:str)->dict:
    '''Scrapes a page with a different HTML structure'''
    logging.info(f'Using our Fallback data extraction method for {url}')
#revisit this if the scraper achieves inefficent results



#--------------------------
#Prometheus to track our scraper
from prometheus_client import Counter, start_http_server








async def goto_with_retry(page: Page, url: str, timeout: int = 60000):
    """
    Attempts to navigate to a URL with retry logic for network errors or timeouts.
    """
    logging.info(f"Attempting to go to: {url}")
    await page.goto(url, timeout=timeout, wait_until="load")
    logging.info(f"Successfully navigated to: {url}")


# --- Scraper Functions ---

import logging
from playwright.async_api import Page, TimeoutError


async def scrape_all_pages(page: Page, main_url: str) -> list[str]:
    """
    Navigates through all available pages, extracts all property links, and returns them.
    Includes robust retry logic, random delays, and handles pagination until no more pages are found.
    Ensures unique URLs are returned.
    """
    logging.info(f"Starting multi-page scraping from: {main_url}")
    property_urls_set = set()
    current_page_number = 1

    try:
        # Step 1: Navigate to the initial page.
        await page.goto(main_url, wait_until='domcontentloaded', timeout=60000)

        while True:
            logging.info(f"Scraping page {current_page_number}...")

            # Step 2: Wait for content to load on the current page.

            try:
                await page.wait_for_selector('a.property-link', timeout=30000)
            except TimeoutError:
                logging.warning(f"No property links found on page {current_page_number}, ending pagination.")
                break

            # Add a random delay to mimic human behavior and avoid bot detection.
            await page.wait_for_timeout(1000)

            # Step 3: Extract links from the current page.
            property_links_locators = page.locator('a.property-link')
            count = await property_links_locators.count()
            logging.info(f"Found {count} potential property links on page {current_page_number}.")

            for i in range(count):
                href = await property_links_locators.nth(i).get_attribute('href')
                if href:
                    # Ensure URLs are absolute.
                    if not href.startswith('http'):
                        href = page.url.rstrip('/') + '/' + href.lstrip('/')
                    property_urls_set.add(href)

            # Step 4: Check for the "next page" button and break the loop if it's not found.
            # CRITICAL: Inspect the target website's HTML to find the correct selector for the "next page" button.
            # Common selectors include: 'a.pagination-next', 'a[rel="next"]', 'li.next a', etc.
            next_page_button = page.locator('a.next')

            if not await next_page_button.is_visible() or await next_page_button.is_disabled():
                logging.info("No more pages found. Ending pagination.")
                break

            # Step 5: Click the "next page" button and wait for the new page to load.
            logging.info("Clicking the 'next' page button...")
            await next_page_button.click()
            logging.info("button found and clicked")
            await page.wait_for_selector('a.property-link')

            current_page_number += 1
            await page.wait_for_timeout(1000)  # Small delay between clicks.

    except Exception as e:
        logging.error(f"Error during multi-page scraping: {e}")

    property_urls = list(property_urls_set)
    logging.info(f"Scraping complete. Extracted {len(property_urls)} unique property URLs.")
    return property_urls

async def scrape_apartment_page(page: Page, url: str) -> dict:
    """
    Visits each URL extracted from the main page and scrapes detailed apartment information.
    Includes robust error handling for individual data points, and extracts a limited
    number of floor plans.
    """
    logging.info(f"Scraping detailed page: {url}")
    data = {
        'title': 'N/A',
        'property_link': url,
        'address': 'N/A',
        'property_reviews': '0',  # Default to '0' if no reviews found
        'listing_verification': 'N/A',
        'lease_options': 'N/A',
        'year_built': 'N/A',
        'price' : "Refer to the pricing and floor plan",
        'street': 'N/A',
        'city': 'N/A',
        'state': 'N/A',
        'zip_code': 'N/A',
        'property_type': "Apartment",  # Added for consistency
        'pricing_and_floor_plans': []  # This will be a list of dictionaries for each floor plan
    }

    # Define selectors for better maintainability
    selectors = {
        'pricecontainer' : '.priceBedRangeInfoContainer',
        'title': 'h1.propertyName',
        'address_container': '.propertyAddressContainer',  # Container for street, city, state, zip
        'street_address': '.delivery-address span',
        'city_state_zip_container': '.propertyAddressContainer h2',  # Container for city, state, zip (as a block)
        'city_span': 'span.address-city',
        'state_zip_container': '.stateZipContainer',  # Specific state/zip container
        'property_reviews': '.reviewRating',
        'listing_verification': 'span.verifedText',  # its verifed and not verified the correct spelling
        'lease_options_container': '.feesPoliciesCard:has-text("Lease Options")',
        'year_built_container': '.feesPoliciesCard:has-text("Property Information") .component-list .column:has-text("Built in")',
        'unit_cards': 'li.unitContainer',
        'apartment_name': '.modelName',
        'rent_price_range': '.rentLabel',
        'bedrooms_attr': 'data-beds',  # Attribute, not a selector
        'bathrooms_attr': 'data-baths',  # Attribute, not a selector
        'sqft_col': '.sqftColumn span:not(.screenReaderOnly)',  # Direct sqft column
        'details_sqft_text': '.detailsTextWrapper span',  # Fallback for sqft if not in column
        'unit': '.unitColumn span[title]',
        'base_rent': '.pricingColumn > span:not(.screenReaderOnly)',
        'availability': '.availableColumn .dateAvailable:not(.screenReaderOnly)',
        'details_link_attr': 'data-unitkey'  # Attribute, not a selector
    }

    try:
        await goto_with_retry(page, url)
        await add_random_delay(2, 7)  # Longer delay after navigating to a detail page

        # --- Wait for essential page elements to load ---
        title_locators=page.locator(selectors['title'])
        is_standard_page= await title_locators.count() > 0

        #if there's the title selectors we scrap using our main scrap logic

        if is_standard_page:
            logging.info('Standard page structure detected')



            # Wait for floor plan sections to load
            #await page.wait_for_selector('div.pricingGridItem', timeout=60000)  # Ensure floor plan container is loaded
            #await page.wait_for_selector('li.unitContainer', timeout=60000)  # Ensure at least one unit container is present

            # --- Extract Main Property Details ---
            data['title'] = await safe_inner_text(page.locator(selectors['title']).first)

            # Extract and parse address components more robustly
            data['street'] = await safe_inner_text(page.locator(selectors['street_address']).first)
            data['city'] = await safe_inner_text(page.locator(selectors['city_state_zip_container']).locator(
                'span.address-city').first)  # Targeted city span
            data['state'] = await safe_inner_text(
                page.locator(selectors['state_zip_container']).locator('span').nth(0))  # First span in stateZipContainer
            data['zip_code'] = await safe_inner_text(
                page.locator(selectors['state_zip_container']).locator('span').nth(1))  # Second span in stateZipContainer

            # Reconstruct full address for consistency
            data['address'] = f"{data['street']}, {data['city']}, {data['state']} {data['zip_code']}"
            # Clean up "N/A" components if any
            data['address'] = ", ".join(filter(lambda x: x != 'N/A', data['address'].split(', '))).strip()

            data['property_reviews'] = await safe_inner_text(page.locator(selectors['property_reviews']).first)
            data['listing_verification'] = await safe_inner_text(page.locator(selectors['listing_verification']).first)

            # Extract Lease Options
            lease_options = []
            lease_options_container = page.locator(selectors['lease_options_container'])
            if await lease_options_container.count() > 0:
                lease_option_elements = lease_options_container.locator('.component-list .column')
                for i in range(await lease_option_elements.count()):
                    option = await safe_inner_text(lease_option_elements.nth(i))
                    if option != "N/A":
                        lease_options.append(option)
            data['lease_options'] = lease_options if lease_options else 'N/A'

            # Extract Year Built
            year_built_locator = page.locator(selectors['year_built_container'])
            year_built_text = await safe_inner_text(year_built_locator)
            year_built = 'N/A'
            if "Built in" in year_built_text:
                try:
                    # Extract year using regex for robustness if needed, or simple split
                    year_built = year_built_text.split('Built in ')[-1].split(' ')[0].strip()
                except IndexError:
                    logging.warning(f"Could not parse year built from '{year_built_text}' for {url}")
            data['year_built'] = year_built

            # --- Extract Pricing and Floor Plans ---
            all_units_data = []
            unit_cards_locators = page.locator(selectors['unit_cards'])
            unit_cards_count = await unit_cards_locators.count()
            logging.info(f"Found {unit_cards_count} pricing and floor plans for {url}. Limiting to 1.")

            # Limit floor plans to a manageable number (e.g., 5) for efficiency and anti-bot.
            # Adjust '5' to any number you need. For testing, starting with 1 or 2 is good.
            limit_floor_plans = min(unit_cards_count, 20)

            for i in range(limit_floor_plans):
                unit_card = unit_cards_locators.nth(i)
                unit_pricing_data = {
                    'apartment_name':"N/A", 'rent_price_range': 'N/A', 'bedrooms': 'N/A',
                    'bathrooms': 'N/A', 'sqft': 'N/A', 'unit': 'N/A',
                    'base_rent': 'N/A', 'availability': 'N/A', 'details_link': 'N/A'
                }

                try:
                    # Extract data relative to the current unit_card using safe helpers
                    unit_pricing_data['apartment_name'] = await safe_inner_text(
                        unit_card.locator(selectors['apartment_name']))
                    unit_pricing_data['rent_price_range'] = await safe_inner_text(
                        unit_card.locator(selectors['rent_price_range']))
                    unit_pricing_data['bedrooms'] = await safe_get_attribute(unit_card, selectors['bedrooms_attr'])
                    unit_pricing_data['bathrooms'] = await safe_get_attribute(unit_card, selectors['bathrooms_attr'])

                    # Robust SQFT extraction logic
                    sqft_val = await safe_inner_text(unit_card.locator(selectors['sqft_col']))
                    if sqft_val == "N/A":  # Fallback if direct column not found or empty
                        details_spans = unit_card.locator(selectors['details_sqft_text'])
                        for j in range(await details_spans.count()):
                            text = await safe_inner_text(details_spans.nth(j))
                            if "Sq Ft" in text:
                                sqft_val = text.replace("Sq Ft", "").strip()
                                break
                    unit_pricing_data['sqft'] = sqft_val

                    unit_pricing_data['unit'] = await safe_inner_text(unit_card.locator(selectors['unit']))
                    unit_pricing_data['base_rent'] = await safe_inner_text(unit_card.locator(selectors['base_rent']))
                    unit_pricing_data['availability'] = await safe_inner_text(unit_card.locator(selectors['availability']))
                    unit_pricing_data['details_link'] = await safe_get_attribute(unit_card, selectors['details_link_attr'])

                    all_units_data.append(unit_pricing_data)

                except Exception as inner_e:
                    logging.warning(f"Failed to scrape some unit details for {url}, unit {i}: {inner_e}")
                    all_units_data.append(unit_pricing_data)  # Append partial data even on inner error

            data['pricing_and_floor_plans'] = all_units_data

            logging.info(f"Finished extraction for standard page: {url}")
        else:
            logging.warning('Standard title not found redirecting to fallback data extraction method')
            # data= scrape_page_with_different_structure(page,url,data)

        SCRAPER_SUCCESS.labels(source=url).inc()
        LISTINGS_SCRAPED.labels(source=url).inc()


    except Exception as e:
        SCRAPER_FAILURES.labels(page=url).inc()

        logging.error(f"Error scraping apartment page {url} after retries: {e}")
        return data  # Return current data (possibly incomplete/N/A) if main scraping fails

    # --- 2. VALIDATE ---
    # The validation status can be set here based on critical fields.
    if data['address'] == 'N/A': #some properties scraped dont contain critical fields like title, pricing and floor plans since they need you to contact owner for the info so we cant use that data to decide whether our scraper scraped the listing well instead i have address since in all properties address is always available so we use that to jusdge our scrapers performance
        data['validation_status'] = 'Failed: Critical Data Missing'
        logging.warning(f"Validation status: Failed for {url}")
        VALIDATION_FAILURES.labels(field=data['validation_status'])
    else:
        data['validation_status'] = 'Success'
        logging.info(f"Validation status: Success for {url}")
        VALIDATION_SUCCESS.labels(field=data['validation_status'])

    return data


# --- Main Orchestration Function (Uses Concurrency) ---
async def main():
    """
    Orchestrates the scraping process, including launching the browser,
    scraping main page, and then detailed property pages concurrently.
    This function correctly uses asyncio.Semaphore for controlled concurrency
    and ensures distinct URLs are scraped.
    """
    start_time=time.time()
    scraped_final_data = []
    try:
        async with async_playwright() as p:
            # Launch Firefox, with anti-detection arguments
            browser = await p.firefox.launch(
                headless=True,  # Set to True for production, False for debugging
                args=["--disable-http2", "--disable-features=AutomationControlled", "--disable-web-security"]
            )
            # Create a new context with a random User-Agent for this session
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))

            # Use a page from the context for the main page scraping
            main_page_instance = await context.new_page()
            main_url = 'https://www.apartments.com/chicago-il/'
            property_urls = await scrape_all_pages(main_page_instance, main_url)
            await main_page_instance.close()  # Close main page instance as it's not needed for detail scrapes

            # Limit the number of properties to scrape for faster testing/development

            properties_to_scrape_limit = 100  # Set to 5 as a reasonable test sample
            limited_property_urls = property_urls[:properties_to_scrape_limit]

            logging.info(
                f"Found {len(property_urls)} properties on main page. Proceeding to scrape {len(limited_property_urls)} properties for detail.")

            # Use a semaphore to control concurrency
            max_concurrent_pages = 5  # Reduced concurrency to 3 to be less aggressive. Adjust as needed.
            semaphore = asyncio.Semaphore(max_concurrent_pages)

            tasks = []
            # Create a task for each UNIQUE URL in the limited list
            for url in limited_property_urls:
                tasks.append(scrape_with_semaphore(context, url, semaphore))

            # Run all scraping tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and separate successful scrapes from failures/exceptions
            for res in results:
                if isinstance(res, dict) and res.get('validation_status') == 'Success':
                    scraped_final_data.append(res)
                    LISTINGS_SCRAPED.labels(source=url)
                else:
                    error_msg = str(res) if isinstance(res,
                                                       Exception) else f"Validation Failed: {res.get('property_link', 'N/A')}"
                    logging.error(f"A property scrape failed or was invalid: {error_msg}")
                    SCRAPER_FAILURES.labels(source=url).inc()

            # Ensure all pages opened within the context are closed
            for page_instance in context.pages:
                if not page_instance.is_closed():
                    await page_instance.close()
            await browser.close()

            logging.info(f"Total successful property data entries collected: {len(scraped_final_data)}")

            with open("apartments_data.json", "w", encoding="utf-8") as f:
                json.dump(scraped_final_data, f, ensure_ascii=False, indent=4)
            return scraped_final_data

    except Exception as e:
        RETRIES_ATTEMPTED.labels(source=url)
        logging.critical(f"A critical error occurred in main execution: {e}", exc_info=True)


        with open("apartments_data.json", "w", encoding="utf-8") as f:
            json.dump(scraped_final_data,f, ensure_ascii=False, indent=4)
        return scraped_final_data
    # Return whatever data was collected before the critical error
    finally:
        stop_time = time.time()
        total_time_taken = stop_time - start_time
        logging.info(f"It has taken {total_time_taken} seconds to complete.")
        SCRAPE_DURATION.labels(source=url).observe(total_time_taken)

        #update resource packages
        MEMORY_USAGE.set(psutil.virtual_memory().used /1024 / 1024) #MB
        CPU_USAGE.set(psutil.cpu_percent())



async def scrape_with_semaphore(page_context, url: str, semaphore: asyncio.Semaphore) -> dict:
    """
    Acquires a semaphore, creates a new page, scrapes, and releases the semaphore.
    This ensures controlled concurrency for distinct URLs.
    """
    async with semaphore:  # Acquire the semaphore before starting the task
        page = await page_context.new_page()  # A new page is created for each concurrent scrape
        try:
            result = await scrape_apartment_page(page, url)  # Call the main scrape function
            return result
        finally:
            if not page.is_closed():
                await page.close()
            await add_random_delay(1, 3)  # Add a slightly longer delay after each page scrape


# --- Performance Comparison Functions (for Day 4 "Cementing Task") ---
async def run_scraper_mode(headless_mode: bool, p_instance):
    """Runs the scraper in a specified headless mode and returns execution time."""
    start_time = time.time()
    browser = await p_instance.firefox.launch(headless=headless_mode)
    context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
    page = await context.new_page()

    main_url = 'https://www.apartments.com/chicago-il/'
    property_urls = await scrape_all_pages(page, main_url)

    # Limit properties for comparison run to keep it manageable and fast
    comparison_limit = min(len(property_urls), 5)  # Still 5 properties for comparison
    limited_property_urls = property_urls[:comparison_limit]

    logging.info(
        f"Found {len(property_urls)} properties on main page. Scraping {len(limited_property_urls)} for mode comparison.")

    all_properties_data = []
    semaphore = asyncio.Semaphore(3)  # Maintain concurrency limit for comparison runs too

    tasks = []
    for url in limited_property_urls:
        tasks.append(scrape_with_semaphore(context, url, semaphore))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    await browser.close()

    successful_count = sum(1 for res in results if isinstance(res, dict) and res.get('validation_status') == 'Success')
    end_time = time.time()
    return end_time - start_time, successful_count


async def compare_performance():
    """Compares the performance of headless and headed modes."""
    logging.info("\n--- Starting Performance Comparison ---")
    async with async_playwright() as p:
        logging.info("--- Running in HEADLESS mode ---")
        headless_time, headless_count = await run_scraper_mode(True, p)
        logging.info(
            f"Headless mode finished in {headless_time:.2f} seconds, scraped {headless_count} properties successfully.")

        logging.info("--- Running in HEADED mode ---")
        headed_time, headed_count = await run_scraper_mode(False, p)  # Set headless=False

        logging.info(
            f"Headed mode finished in {headed_time:.2f} seconds, scraped {headed_count} properties successfully.")

        if headless_count == headed_count and headless_count > 0:
            logging.info(f"\nPerformance Comparison Summary:")
            logging.info(f"Headless is {(headed_time - headless_time):.2f} seconds faster than Headed.")
        else:
            logging.warning("Counts differ or no properties scraped successfully. Cannot reliably compare performance.")


# --- Main Execution Block ---
if __name__ == '__main__':
    from prometheus_client import start_http_server
    start_http_server(8001)
    scraped_data_output = asyncio.run(main())
    logging.info(f"\nFinal Scraped Data Summary: Collected {len(scraped_data_output)} successful property entries.")
    from db_ops import save_scraped_data_to_db
    #asyncio.run(save_scraped_data_to_db(scraped_data_output))
    #asyncio.run(compare_performance())
