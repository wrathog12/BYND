"""
Pipeline Test: Discovery → Relevancy → Scraper → Summarizer → SQLite
Tests all services together and measures execution time for each stage.
"""

import asyncio
import time
import sys
import os

# Add project root to path so imports resolve correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from backend.app.services.discovery import DiscoveryService
from backend.app.services.relevancy import RelevancyService
from backend.app.services.scraper import ScraperService
from backend.app.services.summary import SummaryService
from backend.app.db.database import init_db, save_articles, get_article_count


async def run_pipeline():
    print("=" * 70)
    print("  BYND AI NEWS — Full Pipeline Test")
    print("  Discovery → Relevancy → Scraper → Summarizer → SQLite")
    print("=" * 70)

    # ── Initialize Database ─────────────────────────────────────────────
    await init_db()

    # ── Stage 1: Discovery ──────────────────────────────────────────────
    print("\n🔍 STAGE 1: Discovery Service (SerpApi)")
    print("-" * 50)

    discovery = DiscoveryService()

    start_discovery = time.perf_counter()
    articles = discovery.fetch_ai_news()
    end_discovery = time.perf_counter()
    discovery_time = end_discovery - start_discovery

    print(f"\n📊 Discovery: {len(articles)} articles in {discovery_time:.1f}s")

    if not articles:
        print("\n⚠️  No articles found. Check your SERPAPI_KEY in .env")
        return

    # ── Stage 2: Relevancy ──────────────────────────────────────────────
    print(f"\n\n🧠 STAGE 2: Relevancy Service (Gemini LLM)")
    print("-" * 50)

    relevancy = RelevancyService()

    start_relevancy = time.perf_counter()
    filtered_articles = await relevancy.filter_articles(articles)
    end_relevancy = time.perf_counter()
    relevancy_time = end_relevancy - start_relevancy

    print(f"\n📊 Relevancy: {len(filtered_articles)} unique events in {relevancy_time:.1f}s")

    if not filtered_articles:
        print("\n⚠️  No articles passed the relevancy filter.")
        return

    # ── Stage 3: Scraper ────────────────────────────────────────────────
    print(f"\n\n🕷️ STAGE 3: Scraper Service (Crawl4AI + Firecrawl)")
    print("-" * 50)

    scraper = ScraperService()

    start_scraper = time.perf_counter()
    scrape_results = await scraper.scrape_articles(filtered_articles)
    end_scraper = time.perf_counter()
    scraper_time = end_scraper - start_scraper

    scraped = scrape_results["scraped"]
    failed = scrape_results["failed"]

    print(f"\n📊 Scraper: {len(scraped)} scraped, {len(failed)} failed in {scraper_time:.1f}s")

    if not scraped:
        print("\n⚠️  No articles were scraped successfully.")
        return

    # ── Stage 4: Summarizer ─────────────────────────────────────────────
    print(f"\n\n📝 STAGE 4: Summary Service (Gemini LLM)")
    print("-" * 50)

    summarizer = SummaryService()

    start_summary = time.perf_counter()
    summarized = await summarizer.summarize_articles(scraped)
    end_summary = time.perf_counter()
    summary_time = end_summary - start_summary

    print(f"\n📊 Summarizer: {len(summarized)} summaries in {summary_time:.1f}s")

    # ── Stage 5: Store in SQLite ────────────────────────────────────────
    print(f"\n\n💾 STAGE 5: Storing in SQLite")
    print("-" * 50)

    start_db = time.perf_counter()
    inserted = await save_articles(summarized)
    end_db = time.perf_counter()
    db_time = end_db - start_db

    counts = await get_article_count()
    print(f"  Inserted: {inserted} articles")
    print(f"  DB Status: {counts}")

    # ── Final Report ────────────────────────────────────────────────────
    total_time = discovery_time + relevancy_time + scraper_time + summary_time + db_time

    print("\n")
    print("=" * 70)
    print("  PIPELINE REPORT")
    print("=" * 70)
    print(f"  📥 Discovered articles          : {len(articles)}")
    print(f"  🧠 Unique events (post-dedup)   : {len(filtered_articles)}")
    print(f"  ✅ Successfully scraped          : {len(scraped)}")
    print(f"  ❌ Failed to scrape              : {len(failed)}")
    print(f"  📝 Summarized                    : {len(summarized)}")
    print(f"  💾 Stored in DB                  : {inserted}")
    print(f"")
    print(f"  ⏱️  Discovery time   : {discovery_time:.1f}s")
    print(f"  ⏱️  Relevancy time   : {relevancy_time:.1f}s")
    print(f"  ⏱️  Scraper time     : {scraper_time:.1f}s")
    print(f"  ⏱️  Summary time     : {summary_time:.1f}s")
    print(f"  ⏱️  DB store time    : {db_time:.1f}s")
    print(f"  ⏱️  TOTAL PIPELINE   : {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  💰 LLM calls         : {(len(articles) + 9) // 10 + (len(scraped) + 4) // 5}")
    print("=" * 70)

    # ── Show Final Articles ─────────────────────────────────────────────
    if summarized:
        print(f"\n✅ FINAL OUTPUT ({len(summarized)} articles):")
        print("-" * 50)
        for i, art in enumerate(summarized, 1):
            dupes = art.get('duplicates_merged', 0)
            dupe_tag = f" (+{dupes} merged)" if dupes > 0 else ""
            summary_words = len(art.get('summary', '').split())
            
            print(f"\n  {i}. {art['title']}{dupe_tag}")
            print(f"     Company  : {art['company_tag']}")
            print(f"     Bucket   : {art.get('bucket', 'N/A')}")
            print(f"     Event    : {art.get('event_label', 'N/A')}")
            print(f"     Method   : {art.get('scrape_method', 'N/A')}")
            print(f"     Words    : {art.get('word_count', 0)} scraped")
            print(f"     Summary  : {art.get('summary', 'N/A')} ({summary_words} words)")
            print(f"     Link     : {art['link']}")

    # ── Show Failed Articles ────────────────────────────────────────────
    if failed:
        print(f"\n❌ FAILED TO SCRAPE ({len(failed)}):")
        print("-" * 50)
        for i, art in enumerate(failed, 1):
            print(f"  {i}. {art['title'][:60]}")
            print(f"     Reason: {art.get('fail_reason', 'Unknown')}")
            print(f"     Link  : {art['link']}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
