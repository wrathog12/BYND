import os
import aiosqlite
from typing import List, Dict, Optional
from datetime import datetime

# DB file lives next to the backend folder
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'bynd_news.db')


async def init_db():
    """Creates the articles table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT UNIQUE NOT NULL,
                source TEXT,
                date TEXT,
                company_tag TEXT NOT NULL,
                bucket TEXT,
                event_label TEXT,
                full_text TEXT,
                summary TEXT,
                word_count INTEGER DEFAULT 0,
                scrape_method TEXT,
                status TEXT DEFAULT 'classified',
                duplicates_merged INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print(f"✅ Database initialized at: {os.path.abspath(DB_PATH)}")


async def save_articles(articles: List[Dict]) -> int:
    """Inserts articles into the database. Skips duplicates by link."""
    async with aiosqlite.connect(DB_PATH) as db:
        inserted = 0
        for art in articles:
            try:
                await db.execute("""
                    INSERT OR REPLACE INTO articles 
                    (title, link, source, date, company_tag, bucket, event_label, 
                     full_text, summary, word_count, scrape_method, status, duplicates_merged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    art.get('title'),
                    art.get('link'),
                    art.get('source'),
                    art.get('date'),
                    art.get('company_tag'),
                    art.get('bucket'),
                    art.get('event_label'),
                    art.get('full_text'),
                    art.get('summary'),
                    art.get('word_count', 0),
                    art.get('scrape_method'),
                    art.get('status', 'classified'),
                    art.get('duplicates_merged', 0)
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️ DB insert error for '{art.get('title', '?')[:40]}': {e}")
        
        await db.commit()
    return inserted


async def get_articles(
    company: Optional[str] = None,
    bucket: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """Retrieves articles with optional filters."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if company:
            query += " AND company_tag = ?"
            params.append(company)
        if bucket:
            query += " AND bucket = ?"
            params.append(bucket)
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_article_count() -> Dict:
    """Returns counts by status for quick stats."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT status, COUNT(*) as count FROM articles GROUP BY status"
        ) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}


async def clear_articles() -> int:
    """Deletes all articles from the DB. Returns number deleted."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM articles")
        count = (await cursor.fetchone())[0]
        await db.execute("DELETE FROM articles")
        await db.commit()
        print(f"🗑️ Cleared {count} articles from database")
        return count
