import asyncio
import aiohttp
import time


url = [
    "https://example.com",
    "https://httpbin.org/delay/3",
    "https://httpbin.org/delay/1"
]

async def fetch(session, url):
    async with session.get(url) as response:
        print(f"Fetched {url} - Status: {response.status}")
        html = await response.text()
        return html

async def main():
    async with aiohttp.ClientSession() as session:
        tasks=[fetch(session, u)for u in url]
        results=await asyncio.gather(*tasks)
        print('All pages fetched')

async def run1():
    start=time.time()
    await main()
    end=time.time()
    print(f"it took {end-start:.2f} seconds to fetch all pages")

asyncio.run(run1())