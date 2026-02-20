import { useState, useEffect, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import ArticleCard from './components/ArticleCard';
import LoadingOverlay from './components/LoadingOverlay';
import { runPipeline, fetchArticles, clearArticles } from './api';
import type { Article, Bucket } from './types';
import { BUCKETS } from './types';
import './index.css';

function App() {
  // ── State ─────────────────────────────────────────────────────
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [selectedNiches, setSelectedNiches] = useState<Bucket[]>([]);
  const [hasLoaded, setHasLoaded] = useState(false);

  // ── Load articles from DB on mount ────────────────────────────
  useEffect(() => {
    loadArticles();
  }, []);

  async function loadArticles() {
    try {
      const data = await fetchArticles({ limit: 200 });
      if (data.articles && data.articles.length > 0) {
        setArticles(data.articles);
        setHasLoaded(true);
      }
    } catch (err) {
      console.log('No existing articles or backend not running yet');
    }
  }

  // ── Pipeline trigger ──────────────────────────────────────────
  async function handleRunPipeline() {
    setIsLoading(true);
    try {
      await runPipeline();
      // After pipeline completes, fetch all articles
      const data = await fetchArticles({ limit: 200 });
      setArticles(data.articles || []);
      setHasLoaded(true);
    } catch (err: any) {
      console.error('Pipeline error:', err);
      const msg = err?.message || 'Unknown error';
      alert(`Pipeline error: ${msg}\n\nMake sure the backend is running on port 8000.`);
    } finally {
      setIsLoading(false);
    }
  }

  // ── Clear DB ──────────────────────────────────────────────────
  async function handleClearDB() {
    if (!confirm('Clear all articles from the database? This cannot be undone.')) return;
    try {
      await clearArticles();
      setArticles([]);
      setHasLoaded(false);
      setSelectedCompanies([]);
      setSelectedNiches([]);
      setSearchQuery('');
    } catch (err) {
      console.error('Clear error:', err);
      alert('Failed to clear database.');
    }
  }

  // ── Filter logic ──────────────────────────────────────────────
  function toggleCompany(company: string) {
    setSelectedCompanies((prev) =>
      prev.includes(company) ? prev.filter((c) => c !== company) : [...prev, company]
    );
  }

  function toggleNiche(niche: Bucket) {
    setSelectedNiches((prev) =>
      prev.includes(niche) ? prev.filter((n) => n !== niche) : [...prev, niche]
    );
  }

  const filteredArticles = useMemo(() => {
    let result = articles;

    // Company filter
    if (selectedCompanies.length > 0) {
      result = result.filter((a) => selectedCompanies.includes(a.company_tag));
    }

    // Niche filter
    if (selectedNiches.length > 0) {
      result = result.filter((a) =>
        selectedNiches.includes(a.bucket?.toUpperCase() as Bucket)
      );
    }

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.title?.toLowerCase().includes(q) ||
          a.summary?.toLowerCase().includes(q) ||
          a.company_tag?.toLowerCase().includes(q)
      );
    }

    return result;
  }, [articles, selectedCompanies, selectedNiches, searchQuery]);

  // ── Company counts (updated dynamically based on niche+search filters) ──
  const companyCounts = useMemo(() => {
    let pool = articles;

    // Apply niche filter to counts
    if (selectedNiches.length > 0) {
      pool = pool.filter((a) =>
        selectedNiches.includes(a.bucket?.toUpperCase() as Bucket)
      );
    }

    // Apply search to counts
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      pool = pool.filter(
        (a) =>
          a.title?.toLowerCase().includes(q) ||
          a.summary?.toLowerCase().includes(q)
      );
    }

    const counts: Record<string, number> = {};
    pool.forEach((a) => {
      counts[a.company_tag] = (counts[a.company_tag] || 0) + 1;
    });
    return counts;
  }, [articles, selectedNiches, searchQuery]);

  // ── Render ────────────────────────────────────────────────────
  return (
    <div className="app-layout">
      <Sidebar
        selectedCompanies={selectedCompanies}
        onToggleCompany={toggleCompany}
        companyCounts={companyCounts}
        onRunPipeline={handleRunPipeline}
        onClear={handleClearDB}
        isLoading={isLoading}
        totalArticles={articles.length}
      />

      <main className="main-content">
        {/* Top Bar */}
        <div className="top-bar">
          <div className="search-bar">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Filter by keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              id="keyword-search"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p className="results-summary">
              Showing <strong>{filteredArticles.length}</strong> articles
              {articles.length > 0 && ` from ${articles.length} total`}.
              {!hasLoaded && " Click 'Advanced Intelligence Search' to start."}
            </p>
          </div>

          {/* Niche Filter Bar */}
          <div className="niche-filter-bar">
            {BUCKETS.map((bucket) => (
              <button
                key={bucket.key}
                className={`niche-toggle ${bucket.css} ${selectedNiches.includes(bucket.key) ? 'active' : ''}`}
                onClick={() => toggleNiche(bucket.key)}
              >
                {bucket.label}
              </button>
            ))}
          </div>
        </div>

        {/* Articles Grid */}
        <div className="articles-grid">
          {filteredArticles.length > 0 ? (
            filteredArticles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                {hasLoaded ? '🔎' : '🚀'}
              </div>
              <h3>
                {hasLoaded
                  ? 'No articles match your filters'
                  : 'Ready to Launch'}
              </h3>
              <p>
                {hasLoaded
                  ? 'Try adjusting your company, niche, or keyword filters.'
                  : 'Click "Advanced Intelligence Search" in the sidebar to fetch and analyze the latest AI news.'}
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Loading Overlay */}
      <LoadingOverlay isVisible={isLoading} />
    </div>
  );
}

export default App;
