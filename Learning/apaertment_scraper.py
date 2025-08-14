import asyncio
from playwright.async_api import async_playwright, Page
import logging
import random
import time



#----RANDOM DELAYS----
async def add_random_delays():
    delay= random.uniform(1,3)
    logging.info(f"Waiting for {delay:.2f} second...")
    await asyncio.sleep(delay)

async def safe_inner_text(page:Page, selector: str, nth: int=0) ->str:
    try:
        locator=page.locator(selector).nth(nth)
        if await locator.count() > 0:
            return(await locator.inner_text()).strip()
    except Exception:
        pass
    return "N/A"


#----USER AGENTS----
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

#configure logging for structured output
logging.basicConfig(level=logging.INFO,format='%(asctime)s -%(levelname)s - %(message)s')



async def scrape_main_page(page:Page, main_url:str):
    '''Navigate to the main page and extract all property links and return them'''
    logging.info(f"Navigating to the main page {main_url}")
    try:
        await page.goto(main_url, timeout=60000)
        await page.wait_for_selector('.mortar-wrapper')


        # Get all property cards links
        property_cards = page.locator('a.property-link')
        count = await property_cards.count()
        logging.info(f"Found {count} properties on the main page")

        await add_random_delays()

        property_urls = []
        for i in range(count):
            href = await property_cards.nth(i).get_attribute('href')
            if href:
                if not href.startswith('http'):
                    href=main_url.rstrip('/')+ '/' + href.lstrip('/')
                property_urls.append(href)
            logging.info(f'Extracted {len(property_urls)} unique property URLs')
        return property_urls
    except Exception as e:
        logging.error(f"Error scrapping main page: {e}")
        return []


async def scrape_apartment_page(page:Page, url:str):
    """Visit's each url extracted from the main page and scrapes details of a single apartment from the url"""
    logging.info(f"Scraping detailed page: {url}")
    data={
        'title': 'N/A',
        'property_link': url,
        'address': 'N/A',
        'property_reviews': 'N/A',
        'listing_verification': 'N/A',
        'lease_options': 'N/A',
        'year_built': 'N/A',
        'city': 'N/A',
        'state': 'N/A',
        'zip_code': 'N/A',
        'pricing_and_floor_plans':[]
    }

    pricing_and_floor_plans={
        'apartment_name': 'N/A',
        'rent_price_range': 'N/A',
        'bedrooms': 'N/A',
        'bathrooms': 'N/A',
        'sqft': 'N/A',
        'unit': 'N/A',
        'base_rent': 'N/A',
        'availability': 'N/A',
        'details_link': 'N/A'
    }
    #selectors to avoid hard coding them

    title_selector="h1.propertyName"
    address_selector=".propertyAddressContainer h2"
    property_reviews_selector="span.reviewRating"
    listing_verification_selector="span.verifedText"
    apartment_name_selector=".priceBedRangeInfo .modelName"
    sqft_selector='.detailsTextWrapper span'
    rent_price_range_selector='.rentLabel'
    bedrooms_selectors='li.unitContainer'
    unit_selectors='li.unitContainer .unitColumn span[title]'
    base_rent_selector='li.unitContainer .pricingColumn > span:not(.screenReaderOnly)'
    availability_selector='li.unitContainer .availableColumn .dateAvailable:not(.screenReaderOnly)'
    details_link_selector='li.unitContainer'
    bathrooms_selectors='li.unitContainer'

    try:
        await page.goto(url,wait_until="networkidle")
        await page.wait_for_selector(title_selector,timeout=30000)

        await add_random_delays()

        title= await page.locator(title_selector).first.inner_text()
        address_random=await page.locator(address_selector).first.inner_text()
        address=" ".join(address_random.split())
        property_reviews=await page.locator(property_reviews_selector).first.inner_text()
        listing_verification= await page.locator(listing_verification_selector).first.inner_text()

        street = await page.locator('.delivery-address span').nth(0).inner_text()
        city = await page.locator('.propertyAddressContainer h2 span').nth(1).inner_text()
        state = await page.locator('.stateZipContainer span').nth(0).inner_text()
        zip_code = await page.locator('.stateZipContainer span').nth(1).inner_text()

        data['title'] = title.strip() if title else "N/A"
        data['address'] = address.strip() if address else "N/A"
        data['property_reviews'] = property_reviews.strip() if property_reviews else "N/A"
        data['listing_verification'] = listing_verification.strip() if listing_verification else "N/A"
        data['property_link'] = url
        data['state']= state
        data['street']=street
        data['city']=city
        data['zipcode']=zip_code




        await add_random_delays()

        lease_options_container = page.locator('.feesPoliciesCard:has-text("Lease Options")')
        lease_options_list = lease_options_container.locator('.component-list .column')
        count = await lease_options_list.count()
        lease_options = []
        for i in range(count):
            option = await lease_options_list.nth(i).inner_text()
            lease_options.append(option.strip())

        data['lease_options'] = lease_options

        year_built_locator = page.locator(
            '.feesPoliciesCard:has-text("Property Information") .component-list .column:has-text("Built in")')
        year_built_text = await year_built_locator.inner_text()
        year_built = 'N/A'
        if "Built in" in year_built_text:
            try:
                year_built = year_built_text.split('Built in ')[-1].split(' ')[0].strip()
            except IndexError:
                pass # year_built remains 'N/A'
        data['year_built'] = year_built

        '''---extracting pricing and floor plans---'''
        all_units_data = []
        unit_cards=page.locator('li.unitContainer')
        unit_card_count= await unit_cards.count()
        logging.info(f"found {unit_card_count} pricing and floor plans for {url}")
        limited_cards=min(unit_card_count,1)

        logging.info(f"Scraping {limited_cards} cards ")

        for i in range(limited_cards):
            unit_card = unit_cards.nth(i)
            apartment_name=await page.locator(apartment_name_selector).first.inner_text()
            async def get_sqft(unit_card):
                sqft_locator = unit_card.locator(".sqftColumn span:not(.screenReaderOnly)")
                if await sqft_locator.count() > 0:
                    return (await sqft_locator.first.inner_text()).strip()

                # If not found, try .detailsTextWrapper and look for 'Sq Ft'
                details_locator = unit_card.locator(".detailsTextWrapper span")
                for j in range(await details_locator.count()):
                    text = (await details_locator.nth(j).inner_text()).strip()
                    if "Sq Ft" in text:
                        return text

                return "N/A"
            text=await get_sqft(unit_card)
            rent_price_range= await page.locator(rent_price_range_selector).inner_text()
            bedrooms=await unit_card.locator(bedrooms_selectors).get_attribute('data-beds')
            unit= await unit_card.locator(unit_selectors).inner_text()
            base_rent=await unit_card.locator(base_rent_selector).inner_text()
            availability=await unit_card.locator(availability_selector).inner_text()
            details_link= await unit_card.locator(details_link_selector).get_attribute('data-unitkey')
            bathrooms= await unit_card.locator(bathrooms_selectors).get_attribute('data-baths')
            unit_data = {
                'apartment_name': apartment_name,
                'rent_price_range': rent_price_range,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'sqft': text,
                'unit': unit,
                'base_rent': base_rent,
                'availability': availability,
                'details_link': details_link
            }
            all_units_data.append(unit_data)
        data['pricing_and_floor_plans']= all_units_data
        logging.info(f"Successfuly scraper {url}")
        return data
    except Exception as error:
        logging.error(f"Error scraping apartment page {url}: {error}")
        return data




async def main():
    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False, args=["--disable-http2", "--disable-features=AutomationControlled", "--disable-web-security"])
            #CREATE A NEW CONTEXT WITH A RANDOM USER AGENT
            context= await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            main_url = 'https://www.apartments.com/chicago-il/'
            property_urls = await scrape_main_page(page, main_url)
            property_urls_to_scrap = property_urls[:1]

            logging.info(f"Found {len(property_urls)} properties to scrap (limited to 1)")


            all_properties_data = [] # Create a list to store all scraped data
            for url in property_urls_to_scrap:
                print(f"Scraping property: {url}")
                property_data = await scrape_apartment_page(page, url)
                all_properties_data.append(property_data) # Append the data to the list
                logging.info(property_data)

            await browser.close()
            return all_properties_data # Return the list after the loop completes
    except Exception as error:
        logging.error(f"An error occurred:{error}")



async def run_scraper_mode(headless_mode: bool,p_instance):
    """Runs the scraper in specified headless mode and returns excecution time"""
    start_time=time.time()
    browser = await p_instance.chromium.launch(headless=headless_mode)
    context= await browser.new_context(user_agent=random.choice(USER_AGENTS))
    page= await context.new_page()

    main_url='https://www.apartments.com/chicago-il/'
    property_urls = await scrape_main_page(page, main_url)
    property_urls=property_urls[:5]

    logging.info(f"Found {len(property_urls)} properties to scrap (limited to 5)")

    all_properties_data = []
    for url in property_urls:
        # Implement random delay here to simulate realistic browsing
        await add_random_delays()
        property_data = await scrape_apartment_page(page, url)
        all_properties_data.append(property_data)

    await browser.close()
    end_time = time.time()
    return end_time - start_time, len(all_properties_data)


async def compare_performance():
    """Compares the performance of headed and headless modes."""
    async with async_playwright() as p:
        logging.info("--- Running in HEADLESS mode ---")
        headless_time, headless_count = await run_scraper_mode(True, p)
        logging.info(f"Headless mode finished in {headless_time:.2f} seconds, scraped {headless_count} properties.")

        logging.info("--- Running in HEADED mode ---")
        headed_time, headed_count = await run_scraper_mode(False, p)  # Set headless=False
        logging.info(f"Headed mode finished in {headed_time:.2f} seconds, scraped {headed_count} properties.")

        if headless_count == headed_count and headless_count > 0:
            logging.info(f"\nPerformance Comparison:")
            logging.info(f"Headless is {headed_time - headless_time:.2f} seconds faster than Headed.")
        else:
            logging.warning("Counts differ or no properties scraped. Cannot reliably compare performance.")


# To run the comparison:
# asyncio.run(compare_performance())

if __name__ == '__main__':
    scraped_data = asyncio.run(main())





