import os
import asyncio
from typing import List, Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class ScraperService:
    def __init__(self):
        self.max_text_length = 15000  # Cap full_text for LLM context
        self.scrape_timeout = 30      # Timeout per article (seconds)
        self.max_concurrent = 5       # Parallel scraping limit
        self.min_word_threshold = 150 # Below this = junk (nav/menus), trigger fallback
        
        # Primary: Crawl4AI (headless browser)
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )
        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=200,
            exclude_external_links=True,
            remove_overlay_elements=True,
            process_iframes=False
        )
        
        # Fallback: Firecrawl (cloud API)
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
        self.firecrawl = FirecrawlApp(api_key=firecrawl_key) if firecrawl_key else None

    async def _scrape_with_crawl4ai(self, crawler, url: str) -> str:
        """Primary scraper using Crawl4AI headless browser."""
        result = await asyncio.wait_for(
            crawler.arun(url=url, config=self.run_config),
            timeout=self.scrape_timeout
        )
        if result.success and result.markdown:
            return result.markdown[:self.max_text_length]
        return ""

    def _scrape_with_firecrawl(self, url: str) -> str:
        """Fallback scraper using Firecrawl cloud API."""
        if not self.firecrawl:
            print(f"      ⚠️ Firecrawl not configured (missing FIRECRAWL_API_KEY)")
            return ""
        try:
            result = self.firecrawl.scrape(
                url, 
                formats=["markdown"]
            )
            markdown = result.markdown if hasattr(result, 'markdown') else ""
            return markdown[:self.max_text_length] if markdown else ""
        except Exception as e:
            print(f"      ⚠️ Firecrawl error: {str(e)[:80]}")
            return ""

    def _has_enough_content(self, text: str) -> bool:
        """Returns True if scraped text meets minimum quality threshold."""
        return len(text.split()) >= self.min_word_threshold

    async def _scrape_single(self, crawler, article: Dict, index: int, total: int, semaphore) -> Dict:
        """Scrapes a single article with primary + fallback strategy."""
        async with semaphore:
            title_short = article['title'][:55]
            print(f"  [{index}/{total}] {title_short}...")
            
            text = ""
            method = ""
            
            # Strategy 1: Crawl4AI (primary)
            try:
                raw = await self._scrape_with_crawl4ai(crawler, article['link'])
                if raw and self._has_enough_content(raw):
                    text = raw
                    method = "crawl4ai"
                elif raw:
                    print(f"    ⚠️ Crawl4AI got only {len(raw.split())} words (junk), trying Firecrawl...")
            except asyncio.TimeoutError:
                print(f"    ⏳ Crawl4AI timeout, trying Firecrawl...")
            except Exception as e:
                print(f"    ⚠️ Crawl4AI failed: {str(e)[:50]}")
            
            # Strategy 2: Firecrawl (fallback) — fires if primary got nothing or junk
            if not text and self.firecrawl:
                try:
                    raw = await asyncio.to_thread(self._scrape_with_firecrawl, article['link'])
                    if raw and self._has_enough_content(raw):
                        text = raw
                        method = "firecrawl"
                    elif raw:
                        print(f"    ⚠️ Firecrawl got only {len(raw.split())} words (below threshold)")
                except Exception as e:
                    print(f"    ⚠️ Firecrawl failed: {str(e)[:80]}")
            
            # Final quality gate: drop anything under 100 words (paywalled/protected junk)
            if text and len(text.split()) < 100:
                print(f"    🗑️ Dropping — only {len(text.split())} words (likely paywall/junk)")
                text = ""
            
            # Result
            if text:
                word_count = len(text.split())
                article['full_text'] = text
                article['word_count'] = word_count
                article['scrape_method'] = method
                article['scrape_status'] = 'scraped'
                print(f"    ✅ {method} ({word_count} words)")
            else:
                article['full_text'] = ""
                article['word_count'] = 0
                article['scrape_method'] = "none"
                article['scrape_status'] = 'failed'
                article['fail_reason'] = "Both scrapers failed or content too short"
                print(f"    ❌ Failed — no usable content")
            
            return article

    async def scrape_articles(self, articles: List[Dict]) -> Dict:
        """
        Scrapes articles with concurrent Crawl4AI + Firecrawl fallback.
        Runs Crawl4AI in a separate thread to avoid Windows asyncio subprocess issues.
        Returns dict with 'scraped' and 'failed' lists.
        """
        print(f"--- Scraping {len(articles)} High-Signal Articles (max {self.max_concurrent} concurrent) ---")
        
        # Run the entire crawl4ai session in a thread with its own event loop
        # to avoid Windows NotImplementedError on make_subprocess_transport
        def _run_crawl4ai_sync():
            """Runs Crawl4AI in a fresh event loop inside a thread."""
            import asyncio as _asyncio
            loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._crawl4ai_batch(articles))
            finally:
                loop.close()
        
        results = await asyncio.to_thread(_run_crawl4ai_sync)

        scraped = [a for a in results if a.get('scrape_status') == 'scraped']
        failed = [a for a in results if a.get('scrape_status') == 'failed']
        
        print(f"\n--- Scraping Complete: {len(scraped)} succeeded, {len(failed)} failed ---")
        if scraped:
            crawl4ai_count = sum(1 for a in scraped if a['scrape_method'] == 'crawl4ai')
            firecrawl_count = sum(1 for a in scraped if a['scrape_method'] == 'firecrawl')
            print(f"    Crawl4AI: {crawl4ai_count} | Firecrawl: {firecrawl_count}")
        
        return {"scraped": scraped, "failed": failed}
    
    async def _crawl4ai_batch(self, articles: List[Dict]) -> List[Dict]:
        """The actual crawl4ai scraping, meant to run in its own event loop."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            tasks = [
                self._scrape_single(crawler, article, i, len(articles), semaphore)
                for i, article in enumerate(articles, 1)
            ]
            results = await asyncio.gather(*tasks)
        
        return results