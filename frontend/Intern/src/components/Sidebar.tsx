import { COMPANIES } from '../types';

interface SidebarProps {
    selectedCompanies: string[];
    onToggleCompany: (company: string) => void;
    companyCounts: Record<string, number>;
    onRunPipeline: () => void;
    onClear: () => void;
    isLoading: boolean;
    totalArticles: number;
}

const COMPANY_ICONS: Record<string, string> = {
    'OpenAI': '◎',
    'Anthropic': 'A',
    'Google Deepmind': 'G',
    'Microsoft': 'M',
    'Meta': '∞',
};

export default function Sidebar({
    selectedCompanies,
    onToggleCompany,
    companyCounts,
    onRunPipeline,
    onClear,
    isLoading,
    totalArticles,
}: SidebarProps) {
    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">B</div>
                <div>
                    <h1>Bynd Intelligence</h1>
                    <span>AI News Dashboard</span>
                </div>
            </div>

            {/* Test Set */}
            <div className="sidebar-section">
                <div className="sidebar-section-title">Test Set</div>
                <div className="test-set-box">
                    <div className="test-set-label">Company Set</div>
                    <div className="test-set-name">AI Companies</div>
                    <div className="test-set-companies">
                        {COMPANIES.map((company) => (
                            <div key={company} className="test-set-company">
                                <span>{COMPANY_ICONS[company]}</span>
                                <span>{company.split(' ').pop()}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Quick Filters */}
            <div className="sidebar-section">
                <div className="sidebar-section-title">Quick Filters</div>
                <div className="quick-filters">
                    {COMPANIES.map((company) => (
                        <button
                            key={company}
                            className={`filter-chip ${selectedCompanies.includes(company) ? 'active' : ''}`}
                            onClick={() => onToggleCompany(company)}
                        >
                            {company}
                            <span className="count-bubble">{companyCounts[company] ?? 0}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Last 7 Days */}
            <div className="sidebar-section">
                <div className="sidebar-section-title">Last 7 Days</div>
                <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                    {totalArticles} articles collected
                </p>
            </div>

            {/* Advanced Search */}
            <button
                className="advanced-search-btn"
                onClick={onRunPipeline}
                disabled={isLoading}
            >
                <span className="sparkle">✨</span>
                Advanced Intelligence Search
            </button>

            {/* Clear Database */}
            {totalArticles > 0 && (
                <button
                    className="advanced-search-btn"
                    onClick={onClear}
                    disabled={isLoading}
                    style={{ background: 'transparent', border: '1px solid #475569', color: '#94a3b8', fontSize: '12px', padding: '10px 16px' }}
                >
                    🗑️ Clear Database ({totalArticles})
                </button>
            )}

            {/* Source Options */}
            <div className="sidebar-section">
                <div className="sidebar-section-title">Sources</div>
                <div className="source-checkboxes">
                    <label className="source-checkbox">
                        <input type="checkbox" defaultChecked />
                        YouTube Transcripts
                    </label>
                    <label className="source-checkbox">
                        <input type="checkbox" />
                        Reddit Posts
                    </label>
                    <label className="source-checkbox">
                        <input type="checkbox" />
                        X (Twitter) Mentions
                    </label>
                </div>
            </div>

            {/* Footer */}
            <div className="sidebar-footer">
                Powered by SerpApi • Gemini • Crawl4AI
            </div>
        </aside>
    );
}
