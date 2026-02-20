import os
import sys
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.app.services.discovery import DiscoveryService
from backend.app.services.relevancy import RelevancyService
from backend.app.services.scraper import ScraperService
from backend.app.services.summary import SummaryService
from backend.app.db.database import init_db, save_articles, get_articles, get_article_count, clear_articles

app = FastAPI(
    title="BYND AI News Intelligence",
    description="News aggregation system with AI-powered classification and summarization",
    version="1.0.0"
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialize services ────────────────────────────────────────────────
discovery_service = DiscoveryService()
relevancy_service = RelevancyService()
scraper_service = ScraperService()
summary_service = SummaryService()


# ── Startup ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ BYND API ready")


# ── Models ─────────────────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    article_ids: List[int]


class PipelineResponse(BaseModel):
    discovered: int
    filtered: int
    scraped: int
    failed: int
    summarized: int
    stored: int


# ── Endpoints ──────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "BYND AI News Intelligence"}


@app.post("/api/pipeline/run", response_model=PipelineResponse)
async def run_pipeline():
    """
    Runs the full pipeline: Discovery → Relevancy → Scraper → Summarizer → DB
    """
    try:
        # Stage 1: Discovery
        articles = discovery_service.fetch_ai_news()
        if not articles:
            raise HTTPException(status_code=404, detail="No articles found from SerpApi")

        # Stage 2: Relevancy (classify + dedup)
        filtered = await relevancy_service.filter_articles(articles)
        if not filtered:
            raise HTTPException(status_code=404, detail="No articles passed relevancy filter")

        # Stage 3: Scrape
        scrape_results = await scraper_service.scrape_articles(filtered)
        scraped = scrape_results["scraped"]
        failed = scrape_results["failed"]

        # Stage 4: Summarize (only scraped articles)
        summarized = []
        if scraped:
            summarized = await summary_service.summarize_articles(scraped)

        # Stage 5: Store in DB
        stored = await save_articles(summarized)

        return PipelineResponse(
            discovered=len(articles),
            filtered=len(filtered),
            scraped=len(scraped),
            failed=len(failed),
            summarized=len(summarized),
            stored=stored
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline crashed: {str(e)}")


@app.get("/api/articles")
async def list_articles(
    company: Optional[str] = Query(None, description="Filter by company tag"),
    bucket: Optional[str] = Query(None, description="Filter by intelligence bucket"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Max results")
):
    """Returns stored articles with optional filters."""
    articles = await get_articles(company=company, bucket=bucket, status=status, limit=limit)
    return {"count": len(articles), "articles": articles}


@app.get("/api/articles/stats")
async def article_stats():
    """Returns article count grouped by status."""
    counts = await get_article_count()
    return {"stats": counts}


@app.post("/api/articles/scrape")
async def scrape_selected(request: ScrapeRequest):
    """
    On-demand: scrape + summarize specific articles by their DB IDs.
    For articles that were stored as 'classified' but not yet scraped.
    """
    # Fetch the articles from DB
    all_articles = await get_articles(status="classified")
    
    # Filter to requested IDs
    to_scrape = [a for a in all_articles if a['id'] in request.article_ids]
    
    if not to_scrape:
        raise HTTPException(status_code=404, detail="No matching articles found")

    # Scrape
    scrape_results = await scraper_service.scrape_articles(to_scrape)
    scraped = scrape_results["scraped"]

    # Summarize
    summarized = []
    if scraped:
        summarized = await summary_service.summarize_articles(scraped)

    # Update in DB
    stored = await save_articles(summarized)

    return {
        "scraped": len(scraped),
        "failed": len(scrape_results["failed"]),
        "summarized": len(summarized),
        "stored": stored
    }


@app.delete("/api/articles/clear")
async def clear_all_articles():
    """Deletes all articles from the database."""
    deleted = await clear_articles()
    return {"deleted": deleted, "message": f"Cleared {deleted} articles"}
