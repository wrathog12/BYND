import os
import json
import asyncio
from typing import List, Dict
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class SummaryService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        self.system_instructions = """
        You are a financial news summarizer. Your task is to create concise, factual summaries 
        of news articles for a business intelligence dashboard.
        
        ### Rules:
        - Each summary MUST be exactly 30-40 words. No exceptions.
        - Write in third person, past tense.
        - Focus on: WHO did WHAT, the IMPACT, and KEY numbers.
        - No filler words, no opinions, no speculation.
        - If the article text is empty or too short, summarize from the title alone.
        """
        
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=self.system_instructions
        )

    async def _summarize_batch(self, batch: List[Dict]) -> List[Dict]:
        """Sends a batch of articles to the LLM for summarization."""
        
        articles_text = ""
        for i, art in enumerate(batch, 1):
            # Use full_text if available, otherwise just the title
            content = art.get('full_text', '')
            if content and len(content) > 500:
                # Send first 2000 chars — enough for a good summary
                content = content[:2000]
            elif not content:
                content = f"Title: {art['title']}"
            
            articles_text += (
                f"Article {i}:\n"
                f"  Title: {art['title']}\n"
                f"  Company: {art['company_tag']}\n"
                f"  Content: {content}\n\n"
            )

        prompt = f"""
Summarize each of the following {len(batch)} articles in exactly 30-40 words each.

{articles_text}

Respond strictly as a JSON array with {len(batch)} objects, one per article in order:
[
  {{
    "id": 1,
    "summary": "Your 30-40 word summary here"
  }}
]
"""
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            results = json.loads(response.text)
            
            for i, result in enumerate(results):
                if i < len(batch):
                    summary = result.get("summary", "")
                    batch[i]['summary'] = summary
                    batch[i]['status'] = 'summarized'
            
            return batch
            
        except Exception as e:
            print(f"  ⚠️ LLM Summary Error: {e}")
            for art in batch:
                art['summary'] = ""
                art['status'] = 'scrape_only'
            return batch

    async def summarize_articles(self, articles: List[Dict], batch_size: int = 5) -> List[Dict]:
        """Generates 30-40 word summaries for a list of articles in batches."""
        print(f"--- Summarizing {len(articles)} articles (batch size: {batch_size}) ---")
        
        all_summarized = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(articles) + batch_size - 1) // batch_size
            print(f"  📝 Summarizing batch {batch_num}/{total_batches} ({len(batch)} articles)...")
            
            summarized = await self._summarize_batch(batch)
            
            for art in summarized:
                word_count = len(art.get('summary', '').split())
                print(f"    ✅ {art['title'][:50]}... ({word_count} words)")
                all_summarized.append(art)
            
            # Small pause between batches
            await asyncio.sleep(0.3)
        
        print(f"--- Summarization Complete: {len(all_summarized)} articles ---")
        return all_summarized
