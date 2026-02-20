<p align="center">
  <img src="https://img.shields.io/badge/BYND-Intelligence-2563eb?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHJ4PSI0IiBmaWxsPSIjMkQ2M0VCIi8+PHRleHQgeD0iNSIgeT0iMTgiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZm9udC13ZWlnaHQ9ImJvbGQiIGZpbGw9IndoaXRlIj5CPC90ZXh0Pjwvc3ZnPg==&logoColor=white" alt="BYND Intelligence"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Gemini_2.5-Flash-4285f4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
</p>

# 🧠 BYND Intelligence — AI News Aggregation Pipeline

> **Intelligent, real-time AI industry news aggregation** — Discover, classify, scrape, summarize, and serve the most lucrative AI business intelligence, all from a single click.

BYND Intelligence is a full-stack pipeline that monitors the AI landscape across **5 major companies** (OpenAI, Anthropic, Google DeepMind, Microsoft, Meta), filters noise from signal using Gemini 2.5 Flash, and delivers concise 30-40 word summaries through a polished React dashboard.

---

## 📸 Screenshots

<details open>
<summary><b>Dashboard — Sidebar & Filters</b></summary>
<br/>
<p align="center">
  <img src="Screenshot 2026-02-21 041231.png" width="250" alt="Sidebar with company filters and pipeline trigger"/>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="Screenshot 2026-02-21 041220.png" width="450" alt="Niche filter toggles"/>
</p>
<p align="center"><i>Left: Sidebar with company filters, article counts, and the "Advanced Intelligence Search" pipeline trigger.<br/>Right: Niche filter toggles — Financials, Strategic Growth, Innovation, Legal & Risk.</i></p>
</details>

<details open>
<summary><b>Dashboard — Article Cards with Summaries</b></summary>
<br/>
<p align="center">
  <img src="Screenshot 2026-02-21 041212.png" width="850" alt="Article cards with AI-generated summaries"/>
</p>
<p align="center"><i>Article cards showing source favicon, headline, company tag, intelligence bucket, and a Gemini-generated 30-40 word summary.</i></p>
</details>

<details open>
<summary><b>Dashboard — Full Article Grid</b></summary>
<br/>
<p align="center">
  <img src="Screenshot 2026-02-21 035826.png" width="850" alt="Full dashboard article grid"/>
</p>
<p align="center"><i>Two-column responsive article grid with source attribution, relative timestamps, and quick "Read Full Article" links.</i></p>
</details>

---

## 🏗️ Architecture

```mermaid
flowchart TD
    subgraph Frontend["🖥️ Frontend (React + Vite + TypeScript)"]
        UI[Dashboard UI]
        Sidebar[Sidebar Filters]
        Cards[Article Cards]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        API[REST API Layer]
        
        subgraph Pipeline["🔄 5-Stage Pipeline"]
            S1["1️⃣ Discovery\n(SerpApi)"]
            S2["2️⃣ Relevancy\n(Gemini 2.5 Flash)"]
            S3["3️⃣ Scraping\n(Crawl4AI + Firecrawl)"]
            S4["4️⃣ Summarization\n(Gemini 2.5 Flash)"]
            S5["5️⃣ Storage\n(SQLite)"]
        end
    end

    subgraph External["🌐 External APIs"]
        SERP[SerpApi - Google News]
        GEMINI[Gemini 2.5 Flash]
        FIRE[Firecrawl API]
    end

    UI -->|POST /api/pipeline/run| API
    UI -->|GET /api/articles| API
    API --> S1
    S1 --> S2 --> S3 --> S4 --> S5
    S1 -.->|fetch news| SERP
    S2 -.->|classify + dedup| GEMINI
    S3 -.->|fallback scrape| FIRE
    S4 -.->|summarize| GEMINI
    S5 -->|articles JSON| UI

    style Frontend fill:#1e293b,stroke:#3b82f6,color:#fff
    style Backend fill:#0f172a,stroke:#10b981,color:#fff
    style Pipeline fill:#1a1a2e,stroke:#f59e0b,color:#fff
    style External fill:#1e1e2e,stroke:#8b5cf6,color:#fff
```

### Pipeline Stages (Detail)

| Stage | Service | What It Does | Tech |
|-------|---------|--------------|------|
| **1. Discovery** | `discovery.py` | Searches Google News for recent articles about 5 AI companies. Runs 5 parallel SerpApi queries with a 7-day recency window. | SerpApi |
| **2. Relevancy** | `relevancy.py` | Classifies each article into Intelligence Buckets (Financials, Strategic Growth, Innovation, Legal & Risk, Noise). Detects duplicate events across sources. Only relevant, unique articles pass. | Gemini 2.5 Flash |
| **3. Scraping** | `scraper.py` | Extracts full article text using a headless browser. Falls back to Firecrawl cloud API if the primary scraper gets junk (<150 words). Quality gate drops anything under 100 words. | Crawl4AI + Firecrawl |
| **4. Summarization** | `summary.py` | Generates concise, factual 30-40 word summaries focused on WHO did WHAT, the IMPACT, and KEY numbers. | Gemini 2.5 Flash |
| **5. Storage** | `database.py` | Stores articles in SQLite with `INSERT OR REPLACE` for idempotent reruns. | aiosqlite |

### Intelligence Buckets

| Bucket | Color | Description |
|--------|-------|-------------|
| 🟥 **FINANCIALS** | Red | Funding rounds, IPOs, valuations, quarterly earnings, mega-deals |
| 🟩 **STRATEGIC_GROWTH** | Green | Market expansions, partnerships, key leadership changes |
| 🟦 **PRODUCT_INNOVATION** | Blue | Model releases (GPT-5, Gemini 2.0), breakthroughs, API shifts |
| 🟧 **LEGAL_AND_RISK** | Orange | Lawsuits, regulatory investigations, ethical controversies |
| ⬜ **NOISE** | — | Filtered out (tutorials, opinion pieces, generic lists) |

---

## 📁 Project Structure

```
BYND/
├── backend/
│   ├── .env                        # API keys (not committed)
│   ├── app/
│   │   ├── main.py                 # FastAPI app + pipeline endpoint
│   │   ├── services/
│   │   │   ├── discovery.py        # Stage 1: SerpApi news fetcher
│   │   │   ├── relevancy.py        # Stage 2: Gemini classifier + dedup
│   │   │   ├── scraper.py          # Stage 3: Crawl4AI + Firecrawl
│   │   │   └── summary.py          # Stage 4: Gemini summarizer
│   │   └── db/
│   │       └── database.py         # Stage 5: SQLite CRUD
│   └── data/
│       └── bynd_news.db            # SQLite database (auto-created)
│
├── frontend/Intern/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx                # React entry point
│       ├── App.tsx                 # Main app: state, filters, pipeline trigger
│       ├── api.ts                  # API client (fetch wrappers)
│       ├── types.ts                # TypeScript interfaces + constants
│       ├── index.css               # Full design system (blue/white/slate)
│       └── components/
│           ├── Sidebar.tsx         # Company filters, pipeline button, clear DB
│           ├── ArticleCard.tsx     # Article card with summary, flairs, source
│           └── LoadingOverlay.tsx  # Pipeline loading overlay with status messages
│
└── requirements.txt                # Python dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`
- API Keys for: [SerpApi](https://serpapi.com/), [Google Gemini](https://aistudio.google.com/apikey), [Firecrawl](https://firecrawl.dev/) (optional fallback)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/BYND.git
cd BYND
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Crawl4AI requires a one-time browser setup
crawl4ai-setup
```

### 3. Configure Environment Variables

Create `backend/.env` with your API keys:

```env
# backend/.env

SERPAPI_KEY=your_serpapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_key_here    # Optional — used as scraping fallback
```

> **Note:** The `.env` file must be inside the `backend/` directory. The services resolve the path dynamically using `Path(__file__).resolve().parents[2] / ".env"`.

### 4. Start the Backend

```bash
# From the project root (BYND/)
uvicorn backend.app.main:app --reload --port 8000
```

You should see:
```
✅ Database initialized at: .../backend/data/bynd_news.db
✅ BYND API ready
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5. Frontend Setup

```bash
cd frontend/Intern
npm install
npm run dev
```

The dashboard will be available at **http://localhost:5173**

### 6. Run the Pipeline

1. Open **http://localhost:5173** in your browser
2. Click **"✨ Advanced Intelligence Search"** in the sidebar
3. Watch the loading overlay as it processes through all 5 stages
4. Articles appear in the grid, classified and summarized

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pipeline/run` | Runs the full 5-stage pipeline. Returns stage-by-stage counts. |
| `GET` | `/api/articles` | Fetch articles. Query params: `company`, `bucket`, `status`, `limit` |
| `GET` | `/api/articles/stats` | Article counts grouped by status |
| `GET` | `/api/health` | Health check |
| `DELETE` | `/api/articles/clear` | Clears all articles from the database |

### Example: Run Pipeline

```bash
curl -X POST http://localhost:8000/api/pipeline/run
```

**Response:**
```json
{
  "discovered": 50,
  "filtered": 27,
  "scraped": 22,
  "failed": 5,
  "summarized": 22,
  "stored": 22
}
```

### Example: Fetch Articles

```bash
curl "http://localhost:8000/api/articles?company=OpenAI&limit=5"
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SERPAPI_KEY` | ✅ Yes | [SerpApi](https://serpapi.com/) key for Google News searches |
| `GEMINI_API_KEY` | ✅ Yes | [Google Gemini](https://aistudio.google.com/apikey) key for classification + summarization |
| `FIRECRAWL_API_KEY` | ❌ Optional | [Firecrawl](https://firecrawl.dev/) key for fallback scraping |

### Example `.env`

```env
SERPAPI_KEY=abc123def456ghi789
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIRECRAWL_API_KEY=fc-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | Dashboard UI + client-side filtering |
| **Backend** | FastAPI + Uvicorn | REST API + async pipeline orchestration |
| **LLM** | Gemini 2.5 Flash | Article classification + summarization |
| **Search** | SerpApi | Google News aggregation |
| **Scraping** | Crawl4AI + Firecrawl | Full article text extraction |
| **Database** | SQLite (aiosqlite) | Async article storage |
| **Styling** | Vanilla CSS | Blue/white/slate design system |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m 'Add awesome feature'`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for internal use at BYND. All rights reserved.

---

<p align="center">
  Built with ❤️ by the <b>BYND Intelligence</b> team
</p>
