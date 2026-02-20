import type { Article } from '../types';

interface ArticleCardProps {
    article: Article;
}

function getRelativeTime(dateStr: string): string {
    if (!dateStr) return '';

    try {
        const now = new Date();
        const date = new Date(dateStr);
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 7) return date.toLocaleDateString();
        if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        return 'Just now';
    } catch {
        return dateStr;
    }
}

function getSourceIcon(source: string): string {
    const s = (source || '').toLowerCase();
    if (s.includes('techcrunch')) return '⚡';
    if (s.includes('bloomberg')) return '📊';
    if (s.includes('reuters')) return '📰';
    if (s.includes('financial times') || s.includes('ft')) return '📈';
    if (s.includes('verge')) return '▲';
    if (s.includes('youtube')) return '▶️';
    if (s.includes('reddit')) return '🔴';
    if (s.includes('information')) return '📋';
    if (s.includes('nytimes') || s.includes('new york')) return '📰';
    if (s.includes('washingtonpost')) return '🏛️';
    return '📄';
}

function getBucketCSS(bucket: string): string {
    switch (bucket?.toUpperCase()) {
        case 'FINANCIALS': return 'financials';
        case 'STRATEGIC_GROWTH': return 'strategic_growth';
        case 'PRODUCT_INNOVATION': return 'product_innovation';
        case 'LEGAL_AND_RISK': return 'legal_and_risk';
        default: return '';
    }
}

function getBucketLabel(bucket: string): string {
    switch (bucket?.toUpperCase()) {
        case 'FINANCIALS': return 'Financials';
        case 'STRATEGIC_GROWTH': return 'Strategic Growth';
        case 'PRODUCT_INNOVATION': return 'Innovation';
        case 'LEGAL_AND_RISK': return 'Legal & Risk';
        default: return bucket || '';
    }
}

export default function ArticleCard({ article }: ArticleCardProps) {
    const bucketCSS = getBucketCSS(article.bucket);
    const summaryWords = article.summary ? article.summary.split(' ').length : 0;

    return (
        <div className="article-card" id={`article-${article.id}`}>
            {/* Card Header: Source + Timestamp */}
            <div className="card-header">
                <div className="card-source">
                    <div className="source-icon">{getSourceIcon(article.source)}</div>
                    <span className="source-name">{article.source || 'News'}</span>
                </div>
                <span className="card-timestamp">{getRelativeTime(article.created_at)}</span>
            </div>

            {/* Headline */}
            <h3 className="card-headline">{article.title}</h3>

            {/* Flairs */}
            <div className="card-flairs">
                <span className="company-tag">{article.company_tag}</span>
                {bucketCSS && (
                    <span className={`flair-pill ${bucketCSS}`}>
                        {getBucketLabel(article.bucket)}
                    </span>
                )}
            </div>

            {/* Summary */}
            {article.summary && (
                <p className="card-summary">{article.summary}</p>
            )}

            {/* Footer */}
            <div className="card-footer">
                <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="read-btn"
                >
                    Read Full Article →
                </a>
                {summaryWords > 0 && (
                    <span className="card-word-count">{summaryWords} words</span>
                )}
            </div>
        </div>
    );
}
