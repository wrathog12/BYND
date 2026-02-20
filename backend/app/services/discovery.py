import os
from datetime import datetime, timezone, timedelta
from serpapi import GoogleSearch
from dotenv import load_dotenv
from typing import List, Dict
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class DiscoveryService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.companies = ["OpenAI", "Anthropic", "Google Deepmind", "Microsoft", "Meta"]
        self.max_per_company = 15  # Cap: only top N most relevant per company

        # Expanded source blacklist (press wires + tutorial/social sites)
        self.blacklist = [
            # Press wires
            "prnewswire.com", "globenewswire.com", "businesswire.com",
            # Tutorial / listicle sites
            "medium.com", "towardsdatascience.com", "hackernoon.com",
            "makeuseof.com", "howtogeek.com", "analyticsinsight.net",
            # Social / forums
            "reddit.com", "quora.com",
        ]

        # Noise patterns in titles — aligned with Relevancy's NOISE bucket
        self.noise_keywords = [
            "how to", "tutorial", "top 10", "top 5", "best ways",
            "beginner", "guide", "tips for", "what is", "explained",
            "vs.", "comparison", "review:", "opinion:", "podcast",
            "newsletter", "roundup", "weekly wrap", "step by step",
        ]

    def _is_fresh(self, date_str: str) -> bool:
        """Determines freshness using math (Time-Delta) instead of keywords."""
        if not date_str:
            return False
        
        try:
            # 1. Clean the string: Remove ' UTC' so the offset (+0000) can be parsed by %z
            clean_date = date_str.replace(" UTC", "")
            
            # 2. Parse the specific SerpApi format: 02/19/2026, 06:50 PM, +0000
            # Format breakdown: %m/%d/%Y (Date), %I:%M %p (12h Time), %z (Offset)
            article_dt = datetime.strptime(clean_date, "%m/%d/%Y, %I:%M %p, %z")
            
            # 3. Get current UTC time for a fair comparison
            now = datetime.now(timezone.utc)
            
            # 4. Math: Calculate the difference
            delta = now - article_dt
            
            # 5. Return True if the gap is 7 days or less
            return delta.days <= 7
            
        except Exception as e:
            # If the format changes (e.g., back to '2 days ago'), we fallback to True 
            # to avoid losing data, as SerpApi's qdr:w already filters heavily.
            print(f"Date Parsing Warning: {e} for string '{date_str}'")
            return True

    def _is_noise_title(self, title: str) -> bool:
        """Rejects titles that match common noise patterns."""
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.noise_keywords)

    def fetch_ai_news(self) -> List[Dict]:
        all_processed_results = []
        seen_links = set()
        seen_titles = set()

        for company in self.companies:
            params = {
                "engine": "google_news",
                "q": company,  # Simple query — google_news doesn't support complex booleans
                "tbs": "qdr:w",  # CRITICAL: Past 7 days filter — DO NOT REMOVE
                "gl": "us",
                "api_key": self.api_key
            }

            try:
                print(f"--- Fetching: {company} ---")
                search = GoogleSearch(params)
                results = search.get_dict()
                news_items = results.get("news_results", [])

                company_count = 0  # Track per-company cap

                for group in news_items:
                    # Stop if we've hit the per-company cap
                    if company_count >= self.max_per_company:
                        break

                    # google_news nests actual articles inside 'stories'
                    stories = group.get("stories", [])
                    
                    # If no stories, the group itself might be a standalone article
                    if not stories:
                        stories = [group]

                    for item in stories:
                        if company_count >= self.max_per_company:
                            break

                        link = item.get("link")
                        title = item.get("title")
                        date_str = item.get("date")
                        source = item.get("source", {})
                        source_name = source.get("name") if isinstance(source, dict) else source

                        # Skip if missing essential data
                        if not link or not title:
                            continue

                        # Filter 1: 7-day freshness — MUST STAY
                        if not self._is_fresh(date_str):
                            continue
                        
                        # Filter 2: Deduplication
                        if title in seen_titles or link in seen_links:
                            continue
                        
                        # Filter 3: Source blacklist
                        if any(domain in link for domain in self.blacklist):
                            continue

                        # Filter 4: Noise title patterns
                        if self._is_noise_title(title):
                            continue

                        seen_links.add(link)
                        seen_titles.add(title)
                        company_count += 1
                        
                        all_processed_results.append({
                            "title": title,
                            "link": link,
                            "source": source_name,
                            "date": date_str,
                            "company_tag": company
                        })
                    
            except Exception as e:
                print(f"Error for {company}: {e}")
        
        return all_processed_results

if __name__ == "__main__":
    service = DiscoveryService()
    results = service.fetch_ai_news()
    print(f"\nSUCCESS: {len(results)} articles passed all pre-filters.")
    for r in results[:3]:
        print(f"- [{r['company_tag']}] {r['title']} ({r['date']})")