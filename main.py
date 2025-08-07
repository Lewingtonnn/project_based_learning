from fastapi import FastAPI
import aiohttp
import asyncio

app = FastAPI()

urls = [
    "https://example.com",
    "https://httpbin.org/delay/3",
    "https://httpbin.org/delay/1"
]

async def fetch(session, url):
    async with session.get(url) as response:
        print(f"Fetched: {url} - Status: {response.status}")
        html = await response.text()
        return {"url": url, "status": response.status, "snippet": html[:100]}

@app.get("/scrape")
async def scrape():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {"results": results}
from fastapi import FastAPI
import aiohttp
import asyncio

app = FastAPI()

urls = [
    "https://example.com",
    "https://httpbin.org/delay/3",
    "https://httpbin.org/delay/1"
]

async def fetch(session, url):
    async with session.get(url) as response:
        print(f"Fetched: {url} - Status: {response.status}")
        html = await response.text()
        return {"url": url, "status": response.status, "snippet": html[:100]}

@app.get("/scrape")
async def scrape():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {"results": results}
