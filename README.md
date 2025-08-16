# Bootcamp Learning Journey 🚀

This repository documents my daily progress and learning from a backend-focused Python Bootcamp. The goal is to master topics like SQL, PostgreSQL, FastAPI, Docker, APIs, and software engineering best practices.

I’m committing small projects and code snippets every day to track my growth, keep myself accountable, and build a public learning record.

---

## 📅 Daily Progress

| Day | Topic | Description |
|-----|-------|-------------|
| Day 1 | FastAPI Intro +Asyncio and aiohttp| Built my first FastAPI app with endpoints and auto docs.Also worked on the asyncio and aiohttp and compared async with sync programming |
| Day 2 | | Advanced FastAPI | Worked on dependencies, Background tasks, pydantic models and Validation, Response model and type hinting 
| Day 3 |SQL| Learnt SQL from scratch from online resources like SQLbolt and SQLMode and completed the two  |
| Day 4 | PostgreSQL + SQLAlchemy Integration|Worked on SQLMode and light SQLAlchemy, made my own database and connected it to my app using FastAPI |
| Day 5 | Continuation of day 4 and Terraform| Learned how to write a terraform script to deploy my db, seeded my DB and wrote 10 SQL queries to test on the FastAPI endpoint
| Day 6 |Playwright Scraping + Anti-Ban Tactics| Updated my skills on Playwright to the most recent knowledge and practices for Playwright async, built a scraper that will later feed our db implimenting rotating headers and practiced using rotating proxies|
|Day 7 |Async + Retry Logic + Light DAG (Pipeline-Oriented Thinking)| Updated my code to run asynchronously, added retry logic using tenacity and added randomised delays to be more human like. Also compared the perfomance of running the scraper headless=True vs headless= False where i found the headless mode is 31.4584 seconds faster. Also upgraded the code to validate results so that in future when i connect it to my db itll be easier|
| Day 8 |PostgreSQL Integration + SQLmodel + Terraform to RDS | applied what was learnt on day 4 to design my Schemas, implememnt the model classes, connect my scraper to my **postgresql database and debloyed my RDS to AWS using terraform script |
|Day 9|FastAPI endpoints|Today was my restday and i only made my api endpoints while also practicing my SQL queries in both sql and python, learned how to use selectinload and other advanced things that i didnt cover on day 3|
|Day 10|...
---

## 📌 Purpose

This is not a polished portfolio — this repo is for documenting **learning in public**. Later, I’ll build refined, client-ready projects in separate repositories.

---

## 🛠️ Tech Stack

- Python
- FastAPI
- PostgreSQL
- Docker
- Git & GitHub

---

## ✅ To-do / Upcoming Topics

- [ ] Middleware & async in FastAPI
- [ ] Advanced PostgreSQL queries
- [ ] Testing with Pytest
- [ ] Full CRUD API with Docker
