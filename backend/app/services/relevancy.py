import os
import json
import asyncio
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class RelevancyService:
    def __init__(self):
        # Initialize Gemini 2.5 Flash (gemini-1.5-flash was shut down Sep 2025)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # This prompt is the 'Gatekeeper' logic
        self.system_instructions = """
        You are a Senior Business Intelligence Analyst. Your task is to classify news articles 
        into 'Lucrative Intelligence Buckets' and detect duplicate events for an AI News Aggregator.
        
        ### Intelligence Buckets:
        1. FINANCIALS: Funding rounds, IPOs, valuations, quarterly earnings, or mega-deals.
        2. STRATEGIC_GROWTH: Market expansions, massive partnerships, or key leadership changes.
        3. PRODUCT_INNOVATION: Significant model releases (e.g. GPT-5, Gemini 2.0), breakthroughs, or major API shifts.
        4. LEGAL_AND_RISK: Lawsuits, regulatory investigations, or ethical controversies.
        5. NOISE: Tutorials, "How-to" guides, generic top-10 lists, opinion pieces, or passing mentions.

        ### Rules:
        - Only mark 'is_relevant: true' if the news fits buckets 1, 2, 3, or 4.
        - If it is 'NOISE', 'is_relevant' must be false.
        - Be highly selective. We only want news that impacts a company's market position.
        
        ### Duplicate Event Detection:
        - Multiple articles may cover the SAME underlying event (e.g. "Nvidia investing $30B in OpenAI" from different sources).
        - Assign the same short 'event_label' string to all articles covering the same event.
        - Among duplicates of the same event, mark ONLY the best article as 'best_of_group: true'.
        - "Best" = most comprehensive headline from the most reputable source.
        - Unique (non-duplicate) articles are always 'best_of_group: true'.
        """
        
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=self.system_instructions
        )

    async def _analyze_batch(self, batch: List[Dict]) -> List[Dict]:
        """Sends a batch of articles to the LLM for classification + dedup in one call."""
        
        # Build the numbered article list for the prompt
        articles_text = ""
        for i, art in enumerate(batch, 1):
            articles_text += (
                f"Article {i}:\n"
                f"  Title: {art['title']}\n"
                f"  Source: {art.get('source', 'Unknown')}\n"
                f"  Company: {art['company_tag']}\n\n"
            )

        prompt = f"""
Analyze the following {len(batch)} articles. For EACH article, classify it and detect duplicates.

{articles_text}

Respond strictly as a JSON array with {len(batch)} objects, one per article in order:
[
  {{
    "id": 1,
    "is_relevant": true/false,
    "bucket": "FINANCIALS" | "STRATEGIC_GROWTH" | "PRODUCT_INNOVATION" | "LEGAL_AND_RISK" | "NOISE",
    "event_label": "Short label for the underlying event",
    "best_of_group": true/false,
    "reasoning": "1-sentence justification"
  }}
]
"""
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            )
            results = json.loads(response.text)
            
            # Merge LLM intelligence back into original article objects
            for i, result in enumerate(results):
                if i < len(batch):
                    batch[i].update({
                        "is_relevant": result.get("is_relevant", False),
                        "bucket": result.get("bucket", "NOISE"),
                        "event_label": result.get("event_label", ""),
                        "best_of_group": result.get("best_of_group", False),
                        "reasoning": result.get("reasoning", "")
                    })
            
            return batch
            
        except Exception as e:
            print(f"LLM Batch Error: {e}")
            # On error, mark all as not relevant to avoid bad data
            for art in batch:
                art["is_relevant"] = False
                art["best_of_group"] = False
            return batch

    def _deduplicate_across_batches(self, articles: List[Dict]) -> List[Dict]:
        """Post-processing: groups by event_label across all batches, keeps only the best per event."""
        
        event_groups: Dict[str, List[Dict]] = {}
        
        for art in articles:
            label = art.get("event_label", "").strip().lower()
            if label not in event_groups:
                event_groups[label] = []
            event_groups[label].append(art)
        
        final = []
        for label, group in event_groups.items():
            # Find the one marked best_of_group by the LLM
            best = next((a for a in group if a.get("best_of_group")), None)
            
            # Fallback: if LLM didn't mark any as best, take the first one
            if not best:
                best = group[0]
            
            # Attach how many duplicates were merged
            best["duplicates_merged"] = len(group) - 1
            final.append(best)
        
        return final

    async def filter_articles(self, articles: List[Dict], batch_size: int = 10) -> List[Dict]:
        """Runs the lucrative filter + dedup on articles in batches of 10."""
        print(f"--- Running Lucrative Filter on {len(articles)} articles (batch size: {batch_size}) ---")
        
        all_analyzed = []
        
        # Process in batches of 10 — last batch handles remainder automatically
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(articles) + batch_size - 1) // batch_size
            print(f"  📦 Processing batch {batch_num}/{total_batches} ({len(batch)} articles)...")
            
            analyzed_batch = await self._analyze_batch(batch)
            
            # Collect only relevant articles for dedup
            for art in analyzed_batch:
                if art.get("is_relevant"):
                    all_analyzed.append(art)
                    print(f"    ✅ [{art['bucket']}] {art['title'][:55]}... | event: {art.get('event_label', '?')}")
            
            # Small pause between batches
            await asyncio.sleep(0.3)

        print(f"\n  🔍 Pre-dedup: {len(all_analyzed)} relevant articles")
        
        # Cross-batch deduplication by event_label
        final_list = self._deduplicate_across_batches(all_analyzed)
        
        print(f"  ✨ Post-dedup: {len(final_list)} unique events")
        print(f"--- Filter Complete ---")
        return final_list