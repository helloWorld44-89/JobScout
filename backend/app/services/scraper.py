import asyncio
import logging
import random
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin, urlparse, urlunparse

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
]

_VIEWPORT = {"width": 1280, "height": 900}
_NAV_TIMEOUT = 30_000  # ms


def _clean_url(raw: str, base: str) -> str:
    """Return an absolute URL stripped of tracking query params."""
    url = urljoin(base, raw)
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


@dataclass
class ScrapedJob:
    title: str
    company: str
    location: str
    url: str
    description: str
    source: str


# ── Indeed ─────────────────────────────────────────────────────────────────

class IndeedScraper:
    source = "indeed"
    _BASE = "https://www.indeed.com"

    async def scrape(self, keywords: str, location: str, pages: int = 2) -> list[ScrapedJob]:
        from playwright.async_api import async_playwright  # type: ignore[import-untyped]

        jobs: list[ScrapedJob] = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                ctx = await browser.new_context(
                    user_agent=random.choice(_USER_AGENTS),
                    viewport=_VIEWPORT,
                    locale="en-US",
                )
                page = await ctx.new_page()

                for p in range(pages):
                    offset = p * 15
                    url = (
                        f"{self._BASE}/jobs"
                        f"?q={quote_plus(keywords)}"
                        f"&l={quote_plus(location)}"
                        f"&start={offset}"
                    )
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT)
                        await asyncio.sleep(random.uniform(1.5, 3.0))
                    except Exception as exc:
                        logger.warning("indeed: navigation error page %d: %s", p, exc)
                        break

                    cards = await page.query_selector_all('[data-jk]')
                    if not cards:
                        break

                    for card in cards:
                        try:
                            title_el = await card.query_selector("h2.jobTitle span")
                            company_el = await card.query_selector('[data-testid="company-name"]')
                            location_el = await card.query_selector('[data-testid="text-location"]')
                            link_el = await card.query_selector("h2.jobTitle a")
                            snippet_el = await card.query_selector(".job-snippet")

                            title = (await title_el.inner_text()).strip() if title_el else ""
                            company = (await company_el.inner_text()).strip() if company_el else ""
                            loc = (await location_el.inner_text()).strip() if location_el else ""
                            href = await link_el.get_attribute("href") if link_el else ""
                            snippet = (await snippet_el.inner_text()).strip() if snippet_el else ""

                            if title and href:
                                jobs.append(ScrapedJob(
                                    title=title,
                                    company=company,
                                    location=loc,
                                    url=_clean_url(href, self._BASE),
                                    description=snippet,
                                    source=self.source,
                                ))
                        except Exception as exc:
                            logger.debug("indeed: card parse error: %s", exc)
                            continue
            finally:
                await browser.close()

        logger.info("indeed: scraped %d jobs", len(jobs))
        return jobs


# ── LinkedIn ───────────────────────────────────────────────────────────────

class LinkedInScraper:
    source = "linkedin"
    _BASE = "https://www.linkedin.com"

    async def scrape(self, keywords: str, location: str, pages: int = 2) -> list[ScrapedJob]:
        from playwright.async_api import async_playwright  # type: ignore[import-untyped]

        jobs: list[ScrapedJob] = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                ctx = await browser.new_context(
                    user_agent=random.choice(_USER_AGENTS),
                    viewport=_VIEWPORT,
                    locale="en-US",
                )
                page = await ctx.new_page()

                for p in range(pages):
                    offset = p * 25
                    url = (
                        f"{self._BASE}/jobs/search"
                        f"?keywords={quote_plus(keywords)}"
                        f"&location={quote_plus(location)}"
                        f"&start={offset}"
                    )
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT)
                        await asyncio.sleep(random.uniform(1.5, 3.0))
                        # scroll to trigger lazy-loaded cards
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await asyncio.sleep(1.0)
                    except Exception as exc:
                        logger.warning("linkedin: navigation error page %d: %s", p, exc)
                        break

                    cards = await page.query_selector_all(".base-card")
                    if not cards:
                        break

                    for card in cards:
                        try:
                            title_el = await card.query_selector("h3.base-search-card__title")
                            company_el = await card.query_selector("h4.base-search-card__subtitle")
                            location_el = await card.query_selector(".job-search-card__location")
                            link_el = await card.query_selector("a.base-card__full-link")

                            title = (await title_el.inner_text()).strip() if title_el else ""
                            company = (await company_el.inner_text()).strip() if company_el else ""
                            loc = (await location_el.inner_text()).strip() if location_el else ""
                            href = await link_el.get_attribute("href") if link_el else ""

                            if title and href:
                                jobs.append(ScrapedJob(
                                    title=title,
                                    company=company,
                                    location=loc,
                                    url=_clean_url(href, self._BASE),
                                    description="",
                                    source=self.source,
                                ))
                        except Exception as exc:
                            logger.debug("linkedin: card parse error: %s", exc)
                            continue
            finally:
                await browser.close()

        logger.info("linkedin: scraped %d jobs", len(jobs))
        return jobs


# ── HiringCafe ─────────────────────────────────────────────────────────────

class HiringCafeScraper:
    """
    Scraper for hiring.cafe — a React SPA, so Playwright is required.
    URL pattern and selectors verified against the site as of mid-2024;
    update _SEARCH_URL and the CSS selectors if the layout changes.
    """

    source = "hiringcafe"
    _BASE = "https://hiring.cafe"
    _SEARCH_URL = "https://hiring.cafe/?searchQuery={keywords}&location={location}"

    async def scrape(self, keywords: str, location: str, pages: int = 2) -> list[ScrapedJob]:
        from playwright.async_api import async_playwright  # type: ignore[import-untyped]

        jobs: list[ScrapedJob] = []
        url = self._SEARCH_URL.format(
            keywords=quote_plus(keywords),
            location=quote_plus(location),
        )

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                ctx = await browser.new_context(
                    user_agent=random.choice(_USER_AGENTS),
                    viewport=_VIEWPORT,
                    locale="en-US",
                )
                page = await ctx.new_page()

                try:
                    await page.goto(url, wait_until="networkidle", timeout=_NAV_TIMEOUT)
                    await asyncio.sleep(random.uniform(2.0, 3.5))
                except Exception as exc:
                    logger.warning("hiringcafe: navigation error: %s", exc)
                    return []

                # scroll-load up to `pages` screens worth of results
                for _ in range(pages - 1):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2.0)

                cards = await page.query_selector_all('[data-testid="job-card"], .job-card, article')
                for card in cards:
                    try:
                        title_el = await card.query_selector(
                            'h2, h3, [data-testid="job-title"], .job-title'
                        )
                        company_el = await card.query_selector(
                            '[data-testid="company-name"], .company-name'
                        )
                        location_el = await card.query_selector(
                            '[data-testid="job-location"], .job-location, .location'
                        )
                        link_el = await card.query_selector("a[href]")

                        title = (await title_el.inner_text()).strip() if title_el else ""
                        company = (await company_el.inner_text()).strip() if company_el else ""
                        loc = (await location_el.inner_text()).strip() if location_el else ""
                        href = await link_el.get_attribute("href") if link_el else ""

                        if title and href:
                            jobs.append(ScrapedJob(
                                title=title,
                                company=company,
                                location=loc,
                                url=_clean_url(href, self._BASE),
                                description="",
                                source=self.source,
                            ))
                    except Exception as exc:
                        logger.debug("hiringcafe: card parse error: %s", exc)
                        continue
            finally:
                await browser.close()

        logger.info("hiringcafe: scraped %d jobs", len(jobs))
        return jobs


# ── Orchestrator ───────────────────────────────────────────────────────────

SCRAPERS: dict[str, type] = {
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
    "hiringcafe": HiringCafeScraper,
}


async def run_scrape(
    keywords: str,
    location: str,
    sources: list[str],
) -> list[ScrapedJob]:
    """Run all requested scrapers concurrently and return combined results."""
    tasks = [
        SCRAPERS[src]().scrape(keywords, location)  # type: ignore[call-arg]
        for src in sources
        if src in SCRAPERS
    ]
    if not tasks:
        return []

    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs: list[ScrapedJob] = []
    for src, result in zip(sources, results):
        if isinstance(result, list):
            jobs.extend(result)
        else:
            logger.warning("%s scraper failed: %s", src, result)
    return jobs
