from prometheus_client import Counter, Histogram, Gauge

# ========================
# General Metrics


# ========================
# Core Scraper Metrics
# ========================

# Success / Failures per source
SCRAPER_SUCCESS = Counter(
    "scraper_success_total",
    "Total successful scrapes",
    ["source"]
)

SCRAPER_FAILURES = Counter(
    "scraper_failures_total",
    "Total failed scrapes",
    ["source"]
)

# Number of listings scraped
LISTINGS_SCRAPED = Counter(
    "listings_scraped_total",
    "Total number of listings scraped",
    ["source"]
)

# Scrape duration
SCRAPE_DURATION = Histogram(
    "scrape_duration_seconds",
    "Time taken for a single scrape (seconds)",
    ["source"]
)

# ========================
# Data Quality Metrics
# ========================

VALIDATION_FAILURES = Counter(
    "data_validation_failures_total",
    "Total validation errors (e.g. missing price, city, year_built)",
    ["source"]
)

DUPLICATE_RECORDS = Counter(
    "duplicate_records_total",
    "Total duplicate records detected before DB insert",
    ["source"]
)

VALIDATION_SUCCESS = Counter(
    "validation_success_counts",
    "number of successful validation",
    ['source']
)

# ========================
# Pipeline / DB Metrics
# ========================

DB_INSERT_FAILURES = Counter(
    "db_insert_failures_total",
    "Total failed DB insert operations",
    ["table"]
)

RETRIES_ATTEMPTED = Counter(
    "scraper_retries_total",
    "Total retry attempts made during scraping",
    ["source"]
)

# ========================
# Resource Usage Metrics
# ========================

# Gauge → represents current values, not counters
MEMORY_USAGE = Gauge(
    "scraper_memory_usage_mb",
    "Current memory usage of the scraper in MB"
)

CPU_USAGE = Gauge(
    "scraper_cpu_usage_percent",
    "Current CPU usage percent of the scraper"
)
